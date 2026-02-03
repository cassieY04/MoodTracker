from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from .users import UserManager
import ast
import random
from datetime import datetime, timedelta
from collections import Counter
from Databases.emologdb import get_emolog_by_id


ai_feedback_bp = Blueprint('ai_feedback', __name__)

#general positive and negative word lists
POSITIVE_WORDS = ["happy", "good", "great", "excited", "love", "wonderful", "amazing", "best", "fun", "joy",
                  "blessed", "lucky", "not bad", "fanstastic", "awesome", "pleased", "satisfied", "grateful",
                  "cheerful", "elated", "overjoyed", "thrilled", "delighted", "joyful", "radiant", "lighthearted",
                  "proud", "relief", "relieved", "confident", "content", "calm", "peaceful", "better", "improving",
                  "progress", "productive", "cute", "sweet", "fun", "laugh", "smile", "smiling", "joke", "humor", "humorous",
                  "pass", "passed", "safe", "secure", "hope", "hopeful", "optimistic", "eager", "energetic", "strong",
                  "healthy", "fit", "beautiful", "smart", "easy", "smooth", "fresh", "clean", "free", "freedom"]
NEGATIVE_WORDS = ["unhappy", "sad", "angry", "stressed", "anxious", "bad", "terrible", "awful", "hate", "frustrated",
                  "lonely", "pain", "sick", "cry", "not good", "aint good", "ain't good", "fail", "failed", "failing",
                  "loss", "lost", "losing", "missed", "missing", "worst", "horrible", "disaster", "mess", "hard",
                  "difficult", "tough", "struggle", "struggling", "stuck", "trapped", "boring", "bored", "annoyed",
                  "irritated", "mad", "furious", "scared", "afraid", "fear", "terrified", "nervous", "uneasy",
                  "dread", "panic", "guilt", "guilty", "shame", "ashamed", "embarrassed", "regret", "jealous", "envy",
                  "tired", "exhausted", "drained", "weak", "hurt", "hurting", "broken", "damaged", "stupid", "useless",
                  "hopeless", "worthless", "pointless", "troubled", "sucks"]

#function to detect context based on keywords
#can detect duplicate spellings but not mispellings
#(e.g. "exammmm" can but not "exan")
def detect_context(text):
    text = text.lower()
    context_map = {
        "academic pressure": [
            "exam", "study", "assignment", "deadline", "test", "school", "grade", "gpa", "class",
            "quiz", "midterm", "final", "thesis", "fyp", "project", "presentation", "lecture", 
            "lab", "semester", "submission", "duedate", "late", "resit", "repeat", 
            "scholarship", "tuition", "fees", "enrollment", "coursework", "syllabus", "lecturer", 
            "tutor", "dean", "campus", "university", "college", "uni", "degree", "diploma",
            "capstone", "internship", "practicum", "viva", "research", "paper", "essay",
            "procrastinate", "cramming", "burnout", "dropout", "academic validation", "library"
            "group project", "study group", "professor", "tutorial", "transcript"
        ],
        "achievement success": [
            "won", "solved", "fixed", "completed", "finished", "accomplished", "award", "prize", 
            "win", "victory", "success", "milestone", "breakthrough", "nailed it", "crushed it", 
            "improvement", "progress", "growth", "finally", "done", "worth it", "paid off", 
            "pass", "passed", "ace", "aced", "distinction", "scored", "high distinction",
            "hired", "promotion", "raise", "offer", "bonus", "accomplished", "success", 
            "celebrate", "successful", "fruitful", "proud"
        ],
        "daily hustle": [
            "busy", "productive", "errands", "cleaning", "cooking", "routine", 
            "grocery", "commute", "traffic", "driving", "walking", "parking", "planning", 
            "journaling", "meditating", "hydration", "water", "laundry", "organized",
        ],
        "emotional release": [
            "cry", "crying", "tears", "sob", "weep", "bawling", "break down", "teary",
            "scream", "yell", "vent", "rant", "explode", "meltdown"
        ],
        "financial stress": [
            "costy", "expensive", "debt", "broke", "loan", "inflation", "poverty", "poor",
            "unaffordable"
        ],
        "financial gain": [
            "save", "savings", "investment", "stocks", "rich", "splurge", "treat myself", 
            "retail therapy", "bonus", "profit", "afford", "cheap", "discount", "on sale",
            "on a sale", "income", "got money", "got some money", "treating myself", "job raise",
            "jackpot", "winning money", "win money", "win some money", "saved"
        ],
        "financial general": [
            "money", "pay", "bill", "rent", "budget", "spend", "price", "cash", "wallet", "bank",
            "transfer", "shopping", "buy", "purchase", "groceries", "salary", "wage"
        ],
        "fatigue": [
            "tired", "sleep", "exhausted", "burnt out", "insomnia", "nap", "drained", "fatigue",
            "all-nighter", "sleepy", "zombie", "caffeine", "coffee", "energy drink", "no sleep", 
            "burnout", "overworked", "collapse", "rest", "bed", "pillow", "woke up",
            "low energy", "lethargic", "dead", "dying", "comatose", "hibernating", "sluggish", 
            "yawning", "snooze", "awake", "sleepless"
        ],
        "fitness": [
            "gym", "workout", "running", "exercise", "cardio", "weights", "lifting", "training", 
            "jogging", "treadmill", "dumbbells", "squat", "pushup", "fitness", "athlete", "sport",
            "swim", "yoga", "pilates", "football", "basketball", "badminton", "hiking", "swim", "dance",
            "volleyball", "cycling", "bike ride", "marathon", "triathlon", "stretching", 
            "skate", "rollerblade", "skiing", "snowboard", "wrestling", "exercising", "exercised"
        ],
        "health general": [
            "doctor", "health", "body", "medicine", "pill", "hospital", "clinic", "weight", "diet", 
            "checkup", "appointment", "surgery", "therapy", "medication", "treatment", "recovery",
            "skin", "symptom", "condition"
        ],
        "health issues": [
            "sick", "pain", "ill", "headache", "hurt", "fever", "flu", "cold", "stomach", "migraine", 
            "nausea", "vomit", "stomachache", "period", "cramps", "injury", "broken", "bleed", 
            "acne", "pimple", "allergy", "asthma", "infection", "virus", "bacteria", "chronic", 
            "diagnosed", "bacterial infection", "viral infection", "fatigue", "cough", "sore throat",
            "runny nose", "dengue", "fungal infection", "covid", "dizzy", "chronic pain", "dehydrated",
            "high blood pressure", "hypertension", "low blood pressure", "hypotension", "diabetes",
        ],
        "health positive": [
            "recover", "recovered", "healed", "cured", "fit", "strong", "well", "healthy", "cure"
        ],
        "hobbies": [
            "game", "music", "read", "art", "draw", "code", "movie", "world of warcraft",
            "gaming", "valorant", "league", "netflix", "binge", "spotify", "concert",
            "travel", "food", "photocard", "drawing", "craft", "knitting", "gardening", "poca",
            "anime", "manga", "series", "cook", "bake", "write", "sing", "guitar", "piano", 
            "stream", "twitch", "youtube", "festival", "cafe", "coffee hopping", "thrifting", 
            "makeup", "skincare", "meditation", "journaling", "podcast", "kpop", "kdrama",
            "podcast", "vlog", "photography", "blog", "diy", "shopping", "fashion", "cpop",
            "songs", "songwriting", "fishing", "camping", "road trip", "hobby", "hobbies"
            "pop", "puzzles", "lego", "board games", "tabletop", "cosplay"
        ],
        "loneliness": [
            "lonely", "alone", "isolated", "nobody", "ignored", "miss", "loneliness", "friendless",
            "left out", "excluded", "no friends", "homesick", "empty", "silence", "quiet", "abandoned",
            "unseen", "unheard", "lone wolf", "no friend", "abandon"
        ],
        "pet": [
            "dog", "cat", "pet", "puppy", "kitten", "fish", "bird", "hamster", "rabbit", "paws", "furry",
            "purr", "bark", "tortoise", "guinea pig", "lizard", "snake", "bird", "parrot", "hedgehog"
        ],
        "positive events": [
            "party", "holiday", "vacation", "trip", "promotion", "celebrate", "winning", "won",
            "ace", "aced", "graduate", "convo", "offer", "hired", "vibe", "chill", "relax", 
            "slay", "gift", "present", "surprise", "lucky", "blessed", "success", "bonus", "award",
            "main character", "thriving", "healing", "productive", "accomplished", "proud", "grateful", 
            "fun", "happy",
        ],
        "relationship general": [
            "friend", "family", "partner", "parents", "roommate", "housemate", "peer", "social", 
            "socialize", "classmate", "colleague", "coworker", "neighbor", "meet up", "hang out", "bf", 
            "boyfriend", "girlfriend", "husband", "wife", "mom", "dad", "mother", "father", "sister", 
            "brother", "sibling", "cousin", "gf", "significant other", "mate", "pal", "buddy",
            "date", "dating"
        ],
        "relationship issues": [
            "argument", "fight", "conflict", "breakup", "toxic", "ghosted", "drama", "gossip", 
            "red flag", "reject", "dumped", "cheated", "ex", "tea", "ick", "betray", "jealous", "annoying", "rude", "mean", "ignore", "ignored",
            "envy", "divorce", "gaslight", "love bomb", "clingy", "distant", "misunderstanding", 
            "codependent", "third wheel", "friendzone", "catfish", "hate", "lie"
        ],
        "relationship positive": [
            "bestie", "bff", "best friend", "squad", "love", "date", "dating", "marriage", 
            "compromise", "apologize", "forgive", "trust", "support", "caring", "quality time", "crush", 
            "deep talk", "vibe", "wholesome", "grateful for them", "soft launch"
        ],
        "self-esteem": [
            "ugly", "fat", "stupid", "hate myself", "useless", "failure", "worthless", "confidence",
            "cringe", "awkward", "insecure", "imposter", "disappointment", "compare", "loser", "dumb", 
            "mistake", "guilt", "shame", "embarrassed", "validation",
            "body image", "skinny", "acne", "looks", "appearance", "unlovable", "not enough", 
            "glow up", "mid", "basic", "try hard", "people pleaser"
        ],
        "social media platform": [
            "instagram", "tiktok", "twitter", "x", "facebook", "snapchat", "xhs", "igtv", "youtube", 
            "wechat", "line", "discord", "reddit", "pinterest", "tumblr", "linkedin", "telegram", 
            "douyin", "weibo", "bilibili", "vk", "quora", "medium", "twitch", "pinterest", "skype", 
            "zoom", "xiaohongshu", "threads", "qq", "messenger", "quora", "teams", "clubhouse",
            "whatsapp"
        ],
        "social media general": [
            "feed", "scroll", "screen", "phone", "notification", "dm", "message", "reply", "live", 
            "subscribe", "post", "upload", "story", "status", "app", "comment", "stream", 
        ],
        "social media negativity": [
            "hate", "bully", "toxic", "envy", "jealous", "fake", "drama", "unfollow", "cancel", "troll",
            "block", "unfollow", "cyberbully", "death threat", "expose", "clout", "flop", "shade", "snub"
        ],
        "social media positive": [
            "viral", "trend", "follower", "influencer", "aesthetic", "verified", "likes", "views",
            "growth", "hit", "like"
        ],
        "technology": [
            "wifi", "internet", "laptop", "pc", "computer", "battery", "pc", "app", "website", "download",
            "loading", "ping", "charge", "screen", "mouse", "keyboard", "software", "update", "charging",
            "coding", "programming", "server", "hosting", "deploy", "git", "database", "backend", "frontend",
            "vsc", "visual studio code", "system", "os", "operating system"
        ],
        "technical difficulties": [
            "bug", "error", "crash", "lag", "slow", "frozen", "update failed", "broken", "blue screen",
            "black screen", "glitch", "disconnect", "disconnecting", "network issue", "server down", 
            "lost data", "corrupted", "unable to submit", "submission failed", "stuck", "freeze", 
            "overheat", "malfunction", "reboot", "restart", "factory reset", "system failure", 
            "high ping", "unresponsive", "technical issue", "dc"
        ],
        "transport general": [
            "bus", "train", "mrt", "lrt", "grab", "taxi", "car", "drive", "road", "commute", "flight",
            "plane", "airport", "ride", "driver"
        ],
        "transport stress": [
            "traffic", "jam", "late", "wait", "parking", "accident", "breakdown", "flat tire", "missed",
            "delay", "delayed", "rush hour"
        ],
        "uncertainty": [
            "future", "career", "plans", "worried", "anxious", "what if", "unknown", "direction", "lost",
            "confused", "choice", "decision", "adulting", "rejection", "waiting", "hopeful", "dream", "goal"
        ],
        "weather": [
            "rain", "hot", "sun", "weather", "storm", "humid", "cold", "gloom", "dark", "snow", "fog"
        ],
        "work general": [
            "job", "boss", "work", "meeting", "career", "colleague", "project", "part-time", 
            "shift", "manager", "client", "interview", "resume", "cv", "coworker", "office", "business", 
            "corporate", "9 to 5", "commute"
        ],
        "work stress": [
            "rude", "overtime", "ot", "quit", "resign", "fired", "micromanage", "toxic workplace", "kpi", 
            "workload", "underpaid", "hustle", "grind", "slack", "teams", "zoom fatigue", "unemployed",
            "job hunt"
        ]
    }
    detected = []
    for category, keywords in context_map.items():
        if any(word in text for word in keywords):
            detected.append(category)
    return detected

def get_encouragement(emotion, contexts):
    """Returns a motivational message based on emotion"""
    messages = {
        "happy": [
            "Keep shining! Your positivity is a gift to those around you.",
            "Savor this feeling. You deserve every bit of this happiness.",
            "Happiness looks good on you! Keep this momentum going.",
            "Love this for you! Keep that main character energy going.",
            "You're glowing today! Soak up every moment.",
            "Manifesting more days like this for you!"
        ],
        "excited": [
            "Ride this wave of energy! You are capable of amazing things.",
            "Your enthusiasm is your superpower today.",
            "Go for it! The world is ready for your energy.",
            "This energy is unmatched! Use it to fuel your passions.",
            "Let's go! Big things are happening for you.",
            "The hype is real! Make the most of this spark."
        ],
        "neutral": [
            "Peace is power. Enjoy the calm in the chaos.",
            "A quiet mind is a creative mind. Use this balance wisely.",
            "It's okay to just 'be'. Not every day needs to be a rollercoaster.",
            "Sometimes a chill day is exactly what the soul needs.",
            "Embrace the stillness. You don't always have to be 'on'."
        ],
        "sad": [
            "This feeling is temporary, but your strength is permanent.",
            "It's okay not to be okay. Be gentle with yourself today.",
            "Stars can't shine without darkness. You will get through this.",
            "It’s okay to rot in bed for a bit if you need to. Your feelings are valid.",
            "Sending you a virtual hug. Take all the time you need to heal.",
            "Even a rainy day serves a purpose. Let yourself feel."
        ],
        "anxious": [
            "You are stronger than your anxiety. One breath at a time.",
            "Don't believe everything you think. You are safe right now.",
            "Focus on what you can control, and let go of what you can't.",
            "Remember to unclench your jaw and drop your shoulders. You got this.",
            "Your anxiety is lying to you. You are more capable than you know.",
            "Rooting yourself in the now. You are here, you are breathing."
        ],
        "stressed": [
            "You have survived 100% of your bad days. You've got this.",
            "Rest is not a reward; it's a necessity. Take a break.",
            "One step at a time. You don't have to solve everything today.",
            "Deep breaths. You don't need to carry the weight of the world.",
            "It's okay to say no and protect your peace.",
            "Progress is still progress, even if it's slow."
        ],
        "angry": [
            "Your feelings are valid, but don't let them consume you.",
            "Take a deep breath. You are in control, not your anger.",
            "Channel this energy into something that serves you, not hurts you.",
            "It's okay to be mad. Just don't let it ruin your peace.",
            "Frustration is natural. Let it out safely, then let it go.",
            "Anger is just passion with nowhere to go. Breathe through it."
        ]
    }
    
    #default fallback
    options = messages.get(emotion, ["Trust the process. You are doing your best."])
    return random.choice(options)

def generate_short_feedback(emotion, reason="", thought=""):
    emotion = emotion.lower()
    full_text = f"{reason} {thought}".lower()

    detected_contexts = detect_context(full_text)

    #mixed emotion check
    #check for specific keywords first
    if "technical difficulties" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's great that you're staying positive even when facing tech challenges!"
            return "It's impressive that you're keeping your head up even when the system is crashing! Resilience is key."
        
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                "It's good to see things working out; staying grounded helps you maintain this steady momentum."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Acknowledging a difficult technical issue without letting it overwhelm you shows great mental clarity."
            return "Handling a technical hurdle with a neutral perspective helps you stay focused on the facts of the situation."
        
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that even amidst technical difficulties you still find reasons to be grateful!"
            return "Technical issues can be really frustrating. Remember to take breaks and not let it get to you."
    
    elif "technology" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's great that you're staying positive even when facing tech challenges!"
            return "It's wonderful that your tech is working well! Smooth sailing ahead."
        
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's good to see things working out; staying grounded helps you maintain this steady momentum."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Dealing with tech issues while maintaining a neutral outlook shows great composure."
            return "Staying focused on your digital tasks. It's good to be in the zone."
        
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that even amidst tech challenges you still find reasons to be grateful!"
            return "Technology can be frustrating at times. Remember to take breaks and not let it get to you."

    elif "achievement success" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's valid to feel bad even after a win." 
            return "Your hard work is paying off! Celebrate these victories, big or small."
        
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "Acknowledging your success while staying grounded shows great maturity."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Success can bring mixed feelings. Don't feel bad for feeling neutral about it."
            return "You achieved something great! It's okay to feel neutral about it."
        
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "Success is heavy work. It's valid to be proud of the result while still feeling the strain of the journey."
            return "It's okay to feel down even after a success. Your feelings are valid."

    elif "academic pressure" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in ["fail", "failed", "failing", "bad grade", "poor result"] + NEGATIVE_WORDS):
                return "It's impressive that you're staying positive despite the academic challenges!"
            return "It sounds like things are going well with your studies! It's great to see your hard work paying off."
        
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great to see that you're feeling great despite having a neutral/balanced approach towards academic pressure."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Don't feel bad for having neutral approach towards academic pressure; stay focused on the task at hand."
            return "Taking a balanced approach to your studies helps you stay consistent without burning out."
        
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that you're finding positivity even amidst academic challenges!"
            elif any(word in full_text for word in ["fail", "failed", "failing", "bad grade", "poor result"] + NEGATIVE_WORDS):
                return "School can be tough. Take it one assignment at a time."
            return "School can be tough. Take it one assignment at a time."
    
    elif "work stress" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "Although work is stressful, it's impressive that you're maintaining a positive outlook!"
            return "It's impressive that you're maintaining a positive outlook despite work stress!"
            
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great to see that you're feeling great despite having a neutral/balanced approach towards work stress."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Don't feel bad for having neutral approach towards work stress; stay focused on the task at hand."
            return "Work stress can be draining. It's okay to feel neutral about it sometimes."
            
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that even amidst work stress you still find reasons to be grateful!"
            return "Work stress can be overwhelming. Remember your value isn't defined by your job."
        
    elif "work general" in detected_contexts:
        if "achievement success" in detected_contexts:
            if emotion in ["happy", "excited"]: 
                if any(word in full_text for word in NEGATIVE_WORDS):
                    return "It's valid to feel bad even after a work success."
                return "Congratulations on your work achievement! Your dedication is truly paying off."
            
            elif emotion == "neutral":
                if any(word in full_text for word in POSITIVE_WORDS):
                    return "You achieved something great at work! It's okay to feel neutral while being proud at the same time about it."
                elif any(word in full_text for word in NEGATIVE_WORDS):
                    return "Taking a neutral/balanced approach despite achieved something at work shows great maturity."
                return "Sometimes having a ordinary day at work is completely normal."
            
            else:
                if any(word in full_text for word in POSITIVE_WORDS):
                    return "Work achievements can come with their own pressures. It's valid to be proud of the result while still feeling the strain of the journey."
                return "It's okay to feel down even after a work success. Your feelings are valid."
        
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's great that you're staying positive even when work is not going well."
            return "It's great that work is going well! Enjoy the productivity."
        
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's okay to have mixed emotions at the same time at work."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Taking a neutral/balanced approach towards despite not having a great time at work shows great maturity."
            return "Sometimes having a ordinary day at work is completely normal."
        
        else:   
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that even amidst work challenges you still find reasons to be grateful!"
            return "It's completely valid to feel overwhelmed by work. Remember to take breaks for yourself."

    elif "financial stress" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's amazing that even with money worries, you're keeping a positive outlook!"
            return "It's impressive that you're staying positive despite these financial hurdles!"
            
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's good to see you making progress; staying grounded while managing your budget is a great habit."
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "Looking at financial challenges objectively helps you stay in control of the situation. Don't feel bad about it."
            return "Managing financial pressure with a calm head helps you make better decisions."
            
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "Even with money worries, it's great that you're finding a silver lining."
            return "Financial burdens are heavy. Take it one day—and one budget step—at a time."

    elif "financial gain" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "A sudden increase in wealth can create a sense of discomfort or fear of losing touch with reality."
            return "It's good to feel secure and proactive about your daily spending and financial tasks."
            
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great to see you're feeling steady and balanced while keeping track of your finances."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Don't feel bad for having a neutral approach towards financial gains."
            return "Staying on top of your bills and budget is a solid habit for long-term peace of mind."
            
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that you're still maintaining positivity despite the stress from financial gains."
            return "A sudden increase in wealth can create a sense of discomfort or fear of losing touch with reality. Hence, your feelings are valid."
    
    elif "financial general" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's impressive that you're maintaining a positive outlook while handling your financial tasks!"
            return "It's good to feel secure and proactive about your daily spending and routine finances."
            
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great to see you're feeling balanced while keeping track of your daily expenses."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Having a neutral approach to routine financial tasks is fine; it's all part of staying organized."
            return "Staying on top of your bills and budget is a solid habit for peace of mind."
        
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that even amidst daily financial chores, you're still finding reasons to be grateful!"
            return "Managing money is a constant task. You're doing the work to keep your finances in order."

    elif "health issues" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "Despite the struggles, it's impressive that you're keeping your spirits up even while feeling unwell!"
            return "Being unwell is tough, but your positive energy will definitely help your recovery!"
        
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that you're feeling good about yourself while dealing with health issues with a calm mind."
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "Managing symptoms with a calm mind helps you focus on what your body needs to heal."
            return "Listening to your body and staying level-headed is the first step toward feeling better."
        
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                 return "It's great that you're finding small comforts even while dealing with health issues."
            return "Being unwell is tough. Please prioritize rest and be gentle with yourself today."

    elif "health positive" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's normal to experience some discomforts while recovering."
            return "Feeling healthy and strong is a great blessing! Enjoy this boost of energy."
        
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "Sounds like things are going well, keep up with the calm mind while recovering!"
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "Managing symptoms with a calm mind helps you focus on what your body needs to heal."
            return "It's good to feel steady and well. Maintaining your health is a rewarding habit."
        
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                "Despite you're frustrated about the discomforts from healing, you're still finding positivity!"
            return "It's normal to get frustrated during the healing process."

    elif "health general" in detected_contexts:
        if emotion == "neutral":
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "Handling medical appointments or routines can be a hassle, but stay focused on the goal of wellness."
            return "Staying on top of your health routines and checkups is a smart way to care for your future self."
            
        return "Your health is your wealth. Taking these steps to manage your body is always worth the effort."

    elif "transport general" in detected_contexts or "transport stress" in detected_contexts:
        if "transport stress" in detected_contexts:
            return "Commuting issues are frustrating. Deep breaths while you wait."
        
        if emotion in ["happy", "excited"]:
            return "Enjoy the journey! Safe travels."
        
        return "Commuting can be tiring. Hope you get to your destination safely."
        
    elif "relationship positive" in detected_contexts:
        if emotion in ["happy", "excited"] or any(word in full_text for word in POSITIVE_WORDS):
            if "emotional release" in detected_contexts:
                return "Sharing your joy with loved ones amplifies the happiness. It's tears of joy!"
        
        elif emotion == "neutral":
            return "It's okay to feel neutral even in the presence of loved ones. Emotions can be complex."

        elif emotion in ["angry", "sad", "anxious", "stressed"] or any(word in full_text for word in NEGATIVE_WORDS):
            if "emotional release" in detected_contexts:
                return "Crying or venting is a healthy way to release built-up emotion, even with supportive people around."
            return "It's okay to feel heavy even when you're around supportive people."
        
        return "It's wonderful to feel supported and connected. Cherish these bonds."
        

    elif "relationship issues" in detected_contexts:
        if emotion in ["happy", "excited"] or any(word in full_text for word in POSITIVE_WORDS):
            if "emotional release" in detected_contexts:
                return "It's great to see you having tears of joy from the challenges in your relationships!"
            return "It's great that you're finding positivity even amidst relationship challenges!"
            
        elif emotion == "neutral":
            return "It's understandable to feel neutral after a tough interaction. Take time to process your feelings."
            
        elif any(word in full_text for word in NEGATIVE_WORDS):
            return "It's okay to feel negative emotions even in relationship issues. Let it out; you'll feel lighter soon."
        
        return "Relationship conflicts are draining. Protect your peace and set boundaries if needed."

    elif "relationship general" in detected_contexts:
        if emotion in ["happy", "excited"] or any(word in full_text for word in POSITIVE_WORDS):
            if "emotional release" in detected_contexts:
                return "It's wonderful to have tears of joy when spending time with loved ones!"
            return "Spending time with loved ones is a great way to boost your mood."
        
        elif emotion in ["angry", "stressed", "sad", "anxious"] or any(word in full_text for word in NEGATIVE_WORDS):
            if "emotional release" in detected_contexts:
                return "Crying or venting about relationship challenges is a healthy way to release built-up emotion."
            return "It's normal that interactions with family or friends can be tough and complicated."
        
        return "Social connections are a key part of life."

    elif "pet" in detected_contexts:
        if emotion in ["happy", "excited"]:
            return "Pets bring so much joy! Enjoy the time with your furry friend."
        return "Pets can be a great comfort during tough times. Maybe spend some time with them today."
            
    elif "fitness" in detected_contexts:
        if emotion in ["happy", "excited"]:
            return "Great job on staying active! Endorphins from exercise are a great mood booster."
        return "It's great that you're moving your body. Remember to rest if you need to."

    elif "hobbies" in detected_contexts:
        if emotion in ["happy", "excited"]:
            return "It's wonderful that your hobbies are bringing you joy! Keep indulging in what you love."
        return "Engaging in activities you love is important; consider revisiting these to lift your mood."
        
    elif "fatigue" in detected_contexts:
        if emotion in ["happy", "excited"]:
            return "It is great that you are happy, but you seem tired as well. Remember to get some rest."
        
        elif emotion == "neutral":
            return "Feeling tired can make everything feel a bit more muted. Make sure to prioritize rest."
        
        else:
            return "You seem tired. Remember that rest is productive too."

    elif "positive events" in detected_contexts:
        if emotion in ["sad", "angry", "stressed", "anxious"] or any(word in full_text for word in NEGATIVE_WORDS):
            return f"It seems like a significant event happened ({reason}). It's okay to have mixed feelings about it."
        return "It's wonderful that positive events are happening in your life! Enjoy these moments."
        
    elif "daily hustle" in detected_contexts:
        if emotion in ["happy", "excited"] or any(word in full_text for word in POSITIVE_WORDS):
            return "Amidst the busy hustle, it's great to see you're finding moments of joy!"
        
        elif emotion == "neutral":
            return "A busy day can sometimes feel neutral. Remember to find small moments for yourself."
        
        elif any(word in full_text for word in NEGATIVE_WORDS):
            return "The daily grind can be overwhelming. Make sure to take breaks and care for yourself."
        return "The daily grind can be exhausting. Remember to take breaks and care for yourself."
        
    elif "emotional release" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's wonderful to have tears of joy! Let those happy emotions flow."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Letting out emotions, even happy ones, is healthy. It's okay to have mixed feelings."
            return "It's wonderful to have tears of joy! Let those happy emotions flow."
        
        elif emotion == "neutral":
            return "Crying or venting can be a way to process your emotions, even when feeling neutral."
        
        return "Crying or venting is a healthy way to release built-up emotion. It's okay to let it out."
    
    elif "loneliness" in detected_contexts:
        if emotion in ["happy", "excited"] or any(word in full_text for word in POSITIVE_WORDS):
            return "It's great that you're feeling positive, even when alone. Enjoy your own company!"
            
        elif emotion == "neutral":
            return "It's okay to feel neutral when you're by yourself. Embrace the solitude."
        
        elif any(word in full_text for word in NEGATIVE_WORDS):
            return "Feeling lonely can be tough. Remember that it's okay to reach out to others when you need support."

        return "Crying or venting when feeling lonely is a natural way to cope. You're not alone in this."
        
    elif "social media platform" in detected_contexts:
        if emotion in ["happy", "excited"] or any(word in full_text for word in POSITIVE_WORDS):
            return "It's great that you're enjoying your time on social media platforms!"
            
        elif emotion == "neutral":
                return "It's okay to feel neutral while using social media. Just be mindful of how it affects your mood."

        return "Social media can sometimes bring negative feelings. Remember to take care of your mental health."
    
    elif "social media positive" in detected_contexts:
        if emotion in ["happy", "excited"] or any(word in full_text for word in POSITIVE_WORDS):
            return "It's great that your social media interactions are bringing you joy!"
            
        elif emotion == "neutral":
            return "It's okay to feel neutral about your social media activity. Balance is key."
            
        elif any(word in full_text for word in NEGATIVE_WORDS):
            return "It's good that you're finding some positives even if there are some negativity on social media."

        return "Sometimes social media interactions can be draining. Remember to prioritize your well-being."
        
    elif "social media negativity" in detected_contexts:
        if emotion in ["happy", "excited"] or any(word in full_text for word in POSITIVE_WORDS):
            return "It's impressive that you're maintaining positivity despite negative experiences on social media."
            
        elif emotion == "neutral":
            return "It's understandable to feel neutral after encountering negativity on social media."
            
        return "Negative experiences on social media can be tough. Remember to take breaks."
        
    #if none of the keywords matched, it goes for general emotion based on constant +ve or -ve feedback
    if emotion in ["happy", "excited"] and any(word in full_text for word in NEGATIVE_WORDS):
        return "It seems you're feeling positive, but your notes mention some challenges. It's okay to have mixed feelings."

    if emotion in ["sad", "angry", "stressed", "anxious"] and any(word in full_text for word in POSITIVE_WORDS):
        return "It seems you're feeling down, but your notes mention some positives. It's okay to have mixed feelings."

    if emotion == "neutral":
        if any(word in full_text for word in POSITIVE_WORDS):
             return "You're feeling neutral, but your notes mention some positive things. It sounds like a calm and good moment."
        
        if any(word in full_text for word in NEGATIVE_WORDS):
             return "You're feeling neutral despite some challenges mentioned. Staying balanced is a great strength."
    
    #if no specific context but text is present, reflect it back
    if not detected_contexts and (reason or thought):
        #use emotion to give feedback if can't recognize the context
        target = reason if reason else "your thoughts"
        if emotion in ["happy", "excited"]:
            return f"It's wonderful that {target} is bringing you positivity!"
        
        elif emotion in ["sad", "neutral"]:
            return f"It sounds like {target} is weighing on your mind. Be gentle with yourself."
        
        elif emotion in ["angry"]:
            return f"It seems {target} is causing frustration. It's valid to feel this way."
        
        elif emotion in ["anxious", "stressed"]:
            return f"It sounds like {target} is a source of pressure right now."
        
        return f"It sounds like {target} is impacting you. Feeling {emotion} is valid."
    
    #for if type nothing specific but just general emotion
    if emotion in ["stressed", "anxious"]:
        if reason or thought:
            return (
                "It's okay to feel stressed. You've been dealing with a lot, "
                "and recognizing this is already a positive step."
            )
        return "You seem stressed today. Try to take a short break if possible."

    if emotion == "sad":
        if thought:
            return "Feeling sad can be heavy, especially when thoughts feel overwhelming."
        return "It's okay to feel sad. Be gentle with yourself today."

    if emotion == "angry":
        return "Strong emotions like anger often come from unmet needs or pressure."

    if emotion == "happy":
        return "It's great to see you're feeling happy! Enjoy this moment."

    if emotion == "excited":
        return "Your excitement is contagious! It's a great time to channel that energy."

    if emotion == "neutral":
        return "Feeling neutral is perfectly okay. It's a moment of balance."
    return "Thank you for sharing how you're feeling today."


def generate_full_feedback(emotion, reason="", thought=""):
    emotion = emotion.lower()
    full_text = f"{reason} {thought}".lower()
    
    #analyze separately to distinguish situation (external) vs thoughts (internal)
    reason_contexts = detect_context(reason) if reason else []
    thought_contexts = detect_context(thought) if thought else []
    
    #combined for general checks
    detected_contexts = list(set(reason_contexts + thought_contexts))

    analysis = []
    suggestions = []
    
    #get encouragement based on emotion
    encouragement = get_encouragement(emotion, detected_contexts)

    #mixed emotion checks
    is_mixed_feeling_pos = emotion in ["happy", "excited"] and any(word in full_text for word in NEGATIVE_WORDS)
    is_mixed_feeling_neg = emotion in ["sad", "angry", "stressed", "anxious"] and any(word in full_text for word in POSITIVE_WORDS)
    is_mixed_feeling_neutral_pos = emotion == "neutral" and any(word in full_text for word in POSITIVE_WORDS)
    is_mixed_feeling_neutral_neg = emotion == "neutral" and any(word in full_text for word in NEGATIVE_WORDS)

    #analaysis
    if is_mixed_feeling_pos:
        analysis.append("You've logged a positive emotion, but your notes hint at some negative feelings. This is known as a 'mixed emotional state'.")
        analysis.append("It's completely normal to feel happy about one thing while being worried or sad about another.")
        suggestions.append("Acknowledge both feelings without judgment. They can coexist.")

    elif is_mixed_feeling_neg:
        analysis.append("You've logged a difficult emotion, but your notes contain positive words. This suggests a complex emotional state.")
        analysis.append("It is possible to feel stressed or sad while still acknowledging good things happening around you.")
        suggestions.append("Give yourself credit for noticing the positives despite how you feel.")

    elif is_mixed_feeling_neutral_pos:
        analysis.append("You've logged a neutral mood, but your notes contain positive words.")
        analysis.append("This suggests a sense of calm appreciation or contentment rather than high-energy excitement.")
        suggestions.append("Enjoy this peaceful state of mind.")

    elif is_mixed_feeling_neutral_neg:
        analysis.append("You've logged a neutral mood, but your notes mention negative aspects.")
        analysis.append("This indicates resilience—you are acknowledging difficulties without letting them overwhelm your emotional balance.")
        suggestions.append("Continue to observe these challenges with your current steady perspective.")

    elif emotion in ["stressed", "anxious"]:
        analysis.append("Your emotional state suggests you may be experiencing pressure or overload.")

        if reason:
            analysis.append(f"You identified '{reason}' as a key factor.")
            if reason_contexts:
                analysis.append(f"Specifically, the situation involves {', '.join(reason_contexts)}, which is a common source of pressure.")
            else:
                analysis.append("External stressors like this often contribute to a sense of being overwhelmed, regardless of the specific cause.")
            
            #situation-based on keywords
            if "positive events" in reason_contexts:
                analysis.append("Even positive life changes (eustress) can be physically and mentally draining.")
            
            elif "pet" in reason_contexts:
                analysis.append("Caring for a pet can add responsibilities, which might be contributing to your stress.")
            
            elif "emotional release" in reason_contexts:
                analysis.append("The urge to cry is a natural physiological response to release stress hormones.")
            
            elif "technical difficulties" in reason_contexts:
                analysis.append("Technical glitches or system crashes are frustrating because they disrupt your flow and sense of control.")            
            
            elif "academic pressure" in reason_contexts:
                if "achievement success" in reason_contexts:
                    analysis.append("Even with a success (like passing), the pressure of maintaining grades can still be stressful.")
                else:
                    analysis.append(f"Specifically, {reason} involves academic demands, which are a primary source of your current pressure.")           
            
            elif "work stress" in reason_contexts:
                analysis.append("Toxic or demanding workplace dynamics seem to be weighing on your energy.")
            
            elif "work general" in reason_contexts:
                analysis.append("Professional responsibilities seem to be weighing on your energy.")
            
            elif "hobbies" in reason_contexts:
                analysis.append("Not having enough time for leisure activities can lead to burnout and increased stress.")

            elif "fitness" in reason_contexts:
                analysis.append("Pushing your body too hard without enough recovery can lead to physical and mental stress.")
            
            elif "health issues" in reason_contexts:
                analysis.append("Physical discomfort or illness is a major stressor on the mind and body.")
            
            elif "health general" in reason_contexts:
                analysis.append("General health concerns can subtly contribute to an overall sense of stress.")
            
            elif "transport stress" in reason_contexts:
                analysis.append("Travel delays and traffic are external stressors that feel out of your control.")
            
            elif "achievement success" in reason_contexts:
                analysis.append("Even after achieving success, the pressure to maintain or exceed that level can be stressful.")
            
            elif "relationship postive" in reason_contexts:
                analysis.append("Sometimes, even positive social interactions can lead to overstimulation and stress.")
            
            elif "relationship issues" in reason_contexts:
                analysis.append("Interpersonal conflicts can be a significant source of emotional strain.")
            
            elif "relationship general" in reason_contexts:
                analysis.append("Social dynamics, even in general interactions, can contribute to stress levels.")
            
            elif "loneliness" in reason_contexts:
                analysis.append("Feelings of isolation can heighten stress and anxiety.")

            elif "social media negativity" in reason_contexts:
                analysis.append("Negative experiences on social media can amplify feelings of stress and anxiety.")
            
            elif "social media activity" in reason_contexts:
                analysis.append("High engagement on social media can lead to information overload, contributing to stress.")

            elif "social media platform" in reason_contexts:
                analysis.append("Spending extended time on social media platforms can sometimes increase stress levels due to constant connectivity and exposure to various content.")
            
            elif "financial general" in reason_contexts:
                analysis.append("Managing finances seems to be a source of pressure right now.")
            
            elif "financial stress" in reason_contexts:
                analysis.append("Worries about money can be a heavy burden, contributing significantly to stress.")
            
        if thought:
            if "uncertainty" in thought_contexts:
                analysis.append("Your thoughts are focused on the unknown, which fuels anxiety.")
            
            if "self-esteem" in thought_contexts:
                analysis.append("Your thoughts show a high level of self-expectation, which can intensify your feeling of being overwhelmed.")
            
            else:
                analysis.append("Your thoughts indicate self-expectation or worry, which can intensify stress.")

        suggestions.extend([
            "Break tasks into smaller, manageable steps",
            "Schedule short rest periods between tasks",
            "Write down what you can realistically complete today"
        ])

        if "uncertainty" in detected_contexts:
            analysis.append("Uncertainty about the future can be paralyzing, but taking small steps helps.")
            suggestions.append("Focus on one small thing you can control right now")

    elif emotion == "sad":
        analysis.append("Feeling sad may be linked to emotional fatigue or unmet emotional needs.")

        if reason:
            analysis.append(f"The situation regarding '{reason}' seems to be weighing heavily on you.")
            if "relationship issues" in reason_contexts:
                analysis.append("Interpersonal conflicts can be draining; try to protect your peace.")
            
            elif "pet" in reason_contexts:
                analysis.append("Pets can be a great comfort during tough times. Maybe spend some time with them today.")
            
            elif "loneliness" in reason_contexts:
                analysis.append("Isolation can amplify sadness; connection is often the antidote.")
                suggestions.append("Reach out to a friend or family member, even just for a quick chat")
            
            elif "positive events" in reason_contexts:
                analysis.append("It is valid to feel sad even during happy events. This is often called 'paradoxical emotion'.")
            
            elif "technical difficulties" in reason_contexts:
                analysis.append("It’s valid to feel sad or defeated when tools you rely on fail you during important tasks.")
            
            elif "hobbies" in reason_contexts:
                analysis.append("Engaging in activities you love is important; consider revisiting these to lift your mood.")
            
            elif "academic pressure" in reason_contexts:
                analysis.append("Academic challenges can feel overwhelming and impact your emotional well-being.")
            
            elif "achievement success" in reason_contexts:
                analysis.append("Sometimes after a big achievement, a sense of emptiness or sadness can follow.")
            
            elif "relationship positive" in reason_contexts:
                analysis.append("Even positive social interactions can sometimes stir up unexpected sadness.")
            
            elif "relationship issues" in reason_contexts:
                analysis.append("Conflicts or misunderstandings with loved ones can deeply affect your emotional state.")
            
            elif "relationship general" in reason_contexts:
                analysis.append("Social dynamics, even in general interactions, can influence your mood.")
            
            elif "financial stress" in reason_contexts:
                analysis.append("Worries about money can weigh heavily on your mind and contribute to feelings of sadness.")
            
            elif "financial general" in reason_contexts:
                analysis.append("Financial situations often carry emotional weight.")
            
            elif "health issues" in reason_contexts:
                analysis.append("Dealing with health problems can be physically and emotionally draining.")
            
            elif "health general" in reason_contexts:
                analysis.append("General health concerns can make you feel down.")

            elif "social media negativity" in reason_contexts:
                analysis.append("Negative interactions online can feel personal and isolating.")

            elif "emotional release" in reason_contexts:
                analysis.append("Crying is often a necessary release valve for overwhelming feelings; it helps reset your nervous system.")
            
            elif "social media negativity" in reason_contexts:
                analysis.append("Negative interactions on social media can contribute to feelings of sadness and isolation.")

            elif "social media activity" in reason_contexts:
                analysis.append("Over-engagement with social media can lead to feelings of inadequacy or sadness due to constant comparisons.")

            elif "social media platform" in reason_contexts:
                analysis.append("Spending too much time on social media platforms can sometimes lead to feelings of sadness due to exposure to negative contents.")
            
            elif "fitness" in reason_contexts:
                analysis.append("Lack of physical activity can contribute to feelings of sadness due to lower endorphin levels.")

            if not reason_contexts:
                analysis.append("Sometimes specific events trigger sadness because they touch on deeper values or needs.")

        if thought:
            if "self-esteem" in thought_contexts:
                analysis.append("Your internal monologue seems critical of yourself, which deepens the sadness.")
            
            elif "loneliness" in thought_contexts:
                analysis.append("You are telling yourself that you are alone, but this feeling is temporary.")
   
            if not any(ctx in thought_contexts for ctx in ["uncertainty", "self-esteem"]):
                analysis.append("Your thoughts suggest self-doubt or emotional disappointment.")
            
            if "emotional release" in thought_contexts:
                analysis.append("Thinking about crying indicates you are reaching a point of emotional overflow.")

        suggestions.extend([
            "Allow yourself time to process these feelings",
            "Consider talking to someone you trust",
            "Engage in a calming or comforting activity"
        ])

    elif emotion == "happy":
        analysis.append("Your positive mood suggests emotional balance and satisfaction.")
        
        if reason:
            analysis.append(f"It is great that '{reason}' is bringing you joy.")
            if "technical difficulties" in reason_contexts:
                analysis.append("Staying positive despite technical hurdles is a sign of high resilience.")
            
            elif "achievement success" in reason_contexts:
                analysis.append("You've clearly hit a milestone; acknowledging these wins builds long-term confidence.")
            
            elif "academic pressure" in reason_contexts:
                analysis.append("Finding joy in your studies is a great sign of engagement and progress.")
            
            elif "hobbies" in reason_contexts:
                analysis.append("Engaging in things you love is essential for your mental 'recharge'.")
            
            elif "fitness" in reason_contexts:
                analysis.append("Physical activity releases endorphins, which directly contributes to your happiness.")
            
            elif "pet" in reason_contexts:
                analysis.append("Spending time with your pet is a scientifically proven way to lower stress and boost mood.")
            
            elif "relationship positive" in reason_contexts:
                analysis.append("Positive social connections are a key pillar of happiness and well-being.")
            
            elif "relationship issues" in reason_contexts:
                analysis.append("Overcoming relationship challenges can lead to personal growth and happiness.")
            
            elif "relationship general" in reason_contexts:
                analysis.append("Social interactions, even casual ones, can significantly impact your mood.")
            
            elif "financial" in reason_contexts:
                analysis.append("Financial stability or positive developments can greatly enhance your sense of security and happiness.")
            
            elif "social media activity" in reason_contexts:
                analysis.append("Positive interactions on social media can enhance your sense of community and belonging.")
            
            elif "social media platform" in reason_contexts:
                analysis.append("Enjoying your time on social media platforms can contribute to feelings of connection and joy.")
            
            elif "social media negativity" in reason_contexts:
                analysis.append("Overcoming negative experiences on social media shows your strength and focus on positivity.")
            
            elif "financial gain" in reason_contexts:
                analysis.append("Financial stability or positive developments can greatly enhance your sense of security and happiness.")
            
            elif "financial general" in reason_contexts:
                analysis.append("Feeling good about your financial situation contributes to overall peace of mind.")
            
            elif "health general" in reason_contexts:
                analysis.append("Feeling healthy and strong is a fundamental foundation for happiness.")
            
            elif "health issues" in reason_contexts:
                analysis.append("Overcoming health challenges can lead to a profound appreciation for well-being and happiness.")
            
            elif "transport general" in reason_contexts:
                analysis.append("A smooth journey or drive can be surprisingly relaxing and enjoyable.")

            if not reason_contexts:
                analysis.append("Identifying these personal sources of happiness helps you build resilience.")

        if thought:
            if "self-esteem" in thought_contexts:
                analysis.append("Your thoughts reflect a healthy sense of self-worth right now.")
            
            elif "positive events" in thought_contexts:
                analysis.append("You are actively focusing on the good, which helps strengthen your mental well-being.")
        
        suggestions.extend([
            "Take note of what contributed to this feeling",
            "Try to repeat or maintain these positive habits"
        ])

    elif emotion == "excited":
        analysis.append("Excitement indicates high energy and positive anticipation.")
        
        if reason:
            analysis.append(f"It is wonderful that '{reason}' has sparked this enthusiasm.")
            if "academic pressure" in reason_contexts or "work general" in reason_contexts:
                analysis.append("You're turning a challenge into a motivation—this is a powerful 'flow state'.")
            
            elif "pet" in reason_contexts:
                analysis.append("Pets often bring joy and excitement; it's wonderful you're experiencing that bond.")
            
            elif "social media positive" in reason_contexts:
                analysis.append("Positive digital interactions can be a great way to feel connected to your community.")
            
            elif "social media platform" in reason_contexts:
                analysis.append("Enjoying your time on social media platforms can contribute to feelings of connection and joy.")
            
            elif "social media negativity" in reason_contexts:
                analysis.append("Rising above negative experiences on social media shows your resilience and focus on positivity.")
            
            elif "future uncertainty" in reason_contexts:
                analysis.append("You're viewing the unknown as an opportunity rather than a threat. Keep that perspective!")
            
            elif "hobbies" in reason_contexts:
                analysis.append("Engaging in your passions is fueling this excitement, which is fantastic for your mental health.")
            
            elif "fitness" in reason_contexts:
                analysis.append("Hitting fitness goals or feeling strong is a fantastic source of excitement.")
            
            elif "health general" in reason_contexts:
                analysis.append("Feeling good about your health is a great foundation for excitement about life.")

            elif "health issues" in reason_contexts:
                analysis.append("Overcoming health challenges can lead to a renewed zest for life and excitement about the future.")

            elif "achievement success" in reason_contexts:
                analysis.append("Success is a great motivator; riding this wave can lead to even more accomplishments.")
            
            elif "relationship positive" in reason_contexts:
                analysis.append("Positive social interactions are a great source of excitement and joy.")
            
            elif "relationship issues" in reason_contexts:
                analysis.append("Resolving relationship challenges can lead to renewed excitement about social connections.")
            
            elif "relationship general" in reason_contexts:
                analysis.append("Social connections often bring unexpected joy and excitement.")
            
            elif "financial gain" in reason_contexts:
                analysis.append("Positive financial developments can lead to a sense of freedom and excitement about the future.")
            
            elif "financial general" in reason_contexts:
                analysis.append("Feeling in control of your finances can be very exciting.")
            
            elif "transport general" in reason_contexts:
                analysis.append("Going somewhere new or enjoying a drive is a great mood booster.")
            
            if not reason_contexts:
                analysis.append("Passion for specific interests is a great fuel for mental well-being.")
        
        if thought:
            if "emotional release" in thought_contexts:
                analysis.append("Your excitement is so strong it feels overwhelming; remember to breathe and stay grounded.")
            else:
                analysis.append("Your thoughts are racing with possibilities. This creative energy is a great asset.")

        suggestions.extend([
            "Channel this energy into a creative project",
            "Share your good news with a friend",
            "Write down this moment to remember it later"
        ])

    elif emotion == "neutral":
        analysis.append("A neutral mood signifies stability and a lack of overwhelming emotion.")
        
        if reason:
            analysis.append(f"Your note about '{reason}' suggests a grounded perspective.")
            if "fatigue" in reason_contexts:
                analysis.append("You might be feeling 'flat' because you're physically drained. Neutrality here is your body's way of resting.")
            
            elif "technical difficulties" in reason_contexts:
                analysis.append("Handling tech issues with a neutral head is the most efficient way to problem-solve.")
            
            elif "pet" in reason_contexts:
                analysis.append("Spending time with your pet can be a calming influence, promoting emotional balance.")
            
            elif "academic pressure" in reason_contexts:
                analysis.append("Being objective about your workload helps you prioritize without getting paralyzed by stress.")
            
            elif "fitness" in reason_contexts:
                analysis.append("A neutral mindset during workouts can help you focus on form and consistency rather than intensity.")

            elif "achievement success" in reason_contexts:
                analysis.append("You are celebrating success without getting carried away, which is a sign of emotional maturity.")
            
            elif "relationship positive" in reason_contexts:
                analysis.append("It's ok to feel neutral after a great interaction. You are appreciating social connections in a balanced way.")
            
            elif "relationship issues" in reason_contexts:
                analysis.append("Maintaining neutrality during relationship conflicts helps you stay clear-headed.")
            
            elif "relationship general" in reason_contexts:
                analysis.append("A balanced view of social dynamics is a healthy approach.")
            
            elif "financial general" in reason_contexts:
                analysis.append("A neutral stance on financial matters allows for clear decision-making without emotional bias.")
            
            elif "social media activity" in reason_contexts:
                analysis.append("Engaging with social media in a neutral way helps you avoid emotional ups and downs.")
            
            elif "social media platform" in reason_contexts:
                analysis.append("Using social media platforms with a balanced mindset protects your emotional well-being.")

            elif "social media negativity" in reason_contexts:
                analysis.append("Approaching negative social media experiences with neutrality helps you maintain perspective.")

            elif "health general" in reason_contexts:
                analysis.append("A neutral outlook on health matters allows for practical self-care without emotional overwhelm.")
            
            elif "heatlh issues" in reason_contexts:
                analysis.append("Facing health challenges with a neutral mindset can help you focus on solutions rather than stress.")
            
            if not reason_contexts:
                 analysis.append("Taking a step back to view things neutrally is a valuable skill.")

        if thought:
            if "uncertainty" in thought_contexts:
                analysis.append("You're observing the future without immediate fear, which is a very high level of mindfulness.")
            
            elif "self-esteem" in thought_contexts:
                analysis.append("You are viewing yourself and your progress realistically today, without being too hard on yourself.")    

        suggestions.extend([
            "Use this clarity to plan your week",
            "Practice mindfulness to maintain this balance",
            "Engage in a low-stress hobby like reading"
        ])

    elif emotion == "angry":
        analysis.append("Anger often signals that a boundary has been crossed or a need unmet.")
        
        if reason:
            analysis.append(f"It is understandable that '{reason}' would cause frustration.")
            if "technical difficulties" in reason_contexts:
                analysis.append("Technical glitches are uniquely frustrating because they disrupt your sense of control and progress.")
            
            elif "relationship issues" in reason_contexts:
                analysis.append("Feeling 'hate' or intense anger toward someone usually points to a significant disappointment or broken trust.")
            
            elif "relationship positive" in reason_contexts:
                analysis.append("Sometimes even positive interactions can trigger anger if they highlight unmet needs or boundaries.")

            elif "relationship general" in reason_contexts:
                analysis.append("Even minor social friction can be aggravating when you're already carrying other stressors.")
            
            elif "academic pressure" in reason_contexts:
                analysis.append("When deadlines and expectations feel unfair or overwhelming, anger is a common reaction to that pressure.")
            
            elif "daily hustle" in reason_contexts:
                analysis.append("Constant small errands and a busy schedule can wear down your patience, making small triggers feel much larger.")               
            
            elif "social media negativity" in reason_contexts:
                analysis.append("Encountering negativity on social media can provoke strong emotional reactions, including anger.")
            
            elif "social media activity" in reason_contexts:
                analysis.append("Excessive social media use can lead to feelings of inadequacy or frustration, especially when comparing yourself to others.")

            elif "social media platform" in reason_contexts:
                analysis.append("Social media platforms can sometimes amplify negative emotions due to constant exposure to curated content and comparisons.")
            
            elif "financial stress" in reason_contexts:
                analysis.append("Financial worries can create a backdrop of tension that makes anger more likely to surface.")
            
            elif "health issues" in reason_contexts:
                analysis.append("Dealing with health problems can be frustrating and lead to feelings of anger.")

            if not reason_contexts:
                 analysis.append("Even if the trigger seems specific, anger often points to a need for change or firmer boundaries.")

        if thought:
            if "emotional release" in thought_contexts:
                analysis.append("The urge to vent or 'explode' indicates that your internal pressure has reached a boiling point.")
            
            elif "self-esteem" in thought_contexts:
                analysis.append("Sometimes we direct anger at others when we are actually feeling disappointed in ourselves; be kind to yourself.")
            
            else:
                analysis.append("Your thoughts show you are processing a sense of injustice or unfairness.")

        suggestions.extend([
            "Take a few deep breaths before reacting",
            "Step away from the situation if possible",
            "Write down exactly what frustrated you to clear your mind"
        ])

    else:
        analysis.append(f"You are currently feeling {emotion}, which is a valid emotional response.")
        if reason:
            analysis.append(f"Acknowledging that '{reason}' is affecting you is the first step to managing it.")
             
        suggestions.append("Continue observing your emotions and reflecting on them")

    #general suggestion (fallback & context-specific)
    if "self-esteem" in detected_contexts:
        suggestions.append("Write down 3 things you value about yourself")
        suggestions.append("Remember: social media is a highlight reel, not reality")

    if "academic pressure" in detected_contexts or "work stress" in detected_contexts:
        suggestions.append("Try the Pomodoro technique: 25m focus, 5m break")
        suggestions.append("Celebrate small wins, even just finishing one task")

    if "financial general" in detected_contexts or "financial stress" in detected_contexts:
        suggestions.append("Identify one small change to your budget")
        suggestions.append("Try a 'no-spend' day challenge")
    
    if "social media negativity" in detected_contexts:
        suggestions.append("Consider a short 'digital detox'")
        suggestions.append("Unfollow accounts that drain your energy")
    
    if "health issues" in detected_contexts or "health general" in detected_contexts:
        suggestions.append("Listen to your body and rest if needed")
        suggestions.append("Stay hydrated and prioritize sleep")

    if "pet" in detected_contexts:
        suggestions.append("Spend some therapeutic time with your pet")

    if "fitness" in detected_contexts:
        suggestions.append("Remember to hydrate and stretch after your workout")
        suggestions.append("Track your progress to see how far you've come")

    if "fatigue" in detected_contexts:
        suggestions.append("Prioritize getting a good night's sleep")
        
    if "relationship issues" in detected_contexts or "relationship general" in detected_contexts:
        suggestions.append("Set healthy boundaries to protect your energy")
        suggestions.append("Communicate your needs clearly using 'I' statements")
    
    if "technical difficulties" in detected_contexts:
        suggestions.extend([
            "Step away from the screen for 15 minutes",
            "Try a 'Rubber Duck' debugging session (explain the problem out loud)",
            "Restart your device and take a water break while it boots"
        ])

    if "uncertainty" in detected_contexts:
        suggestions.extend([
            "Write down 3 things that are definitely true right now",
            "Draft a 'Best Case Scenario' to balance out the worries",
            "Talk to a mentor or senior about your path"
        ])

    if "achievement success" in detected_contexts:
        suggestions.extend([
            "Treat yourself to your favorite drink or meal",
            "Take a screenshot of this success to look back on during hard days",
            "Take the rest of the day off if your schedule allows"
        ])
    
    if "work stress" in detected_contexts or "work general" in detected_contexts:
        suggestions.append("Organize your workspace to create a calming environment")
        suggestions.append("Prioritize tasks using the Eisenhower Matrix (Urgent vs Important)")

    #ensure suggestions list is never empty
    if not suggestions:
        if emotion in ["stressed", "anxious", "angry"]:
            suggestions.append("Practice deep breathing exercises (4-7-8 technique)")
            suggestions.append("Take a 10-minute walk to clear your head")
            suggestions.append("Listen to a song that matches your current 'vibe' to process the feeling")
        
        elif emotion in ["sad", "neutral"]:
            suggestions.append("Do one small thing that usually brings you joy")
        
    else:
        suggestions.append("Share your positive energy with someone else")

    #remove duplicates while preserving order
    seen = set()
    suggestions = [x for x in suggestions if not (x in seen or seen.add(x))]

    #limit to 5 suggestions max
    suggestions = suggestions[:5]

    return {
        "emotion": emotion,
        "causes": analysis,
        "suggestions": suggestions,
        "encouragement": encouragement,
        "reflection": {
            "reason": reason,
            "thought": thought
        }
    }
    
def generate_aggregated_feedback(logs, period_name="day"):
    """Generates feedback based on multiple logs (Day, Week, or Month)."""
    #sort logs by time
    logs.sort(key=lambda x: x['timestamp'])
    
    emotions = [l['emotion_name'] for l in logs]
    
    #mood lvl calculations (align with mood statistics graph)
    mood_scores = {
        'Happy': 3, 'Excited': 3,
        'Neutral': 2,
        'Sad': 1, 'Anxious': 1, 'Stressed': 1, 'Angry': 1
    }
    
    scores = [mood_scores.get(e, 2) for e in emotions]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    main_emoji = "😐"
    main_icon = "neutral.png"
    
    #thresholds: 1.0-1.66 (neg), 1.67-2.33 (neu), 2.34-3.0 (pos)
    if avg_score >= 2.34:
        main_emotion = "Mostly Positive"
        main_emoji = "😊"
        main_icon = "happy.png"
    elif avg_score <= 1.66:
        main_emotion = "Mostly Negative"
        main_emoji = "😔"
        main_icon = "sad.png"
    else:
        #check if it's stable neutral or mixed, when it's in neutral range (approx 2.0)
        has_pos = any(s == 3 for s in scores)
        has_neg = any(s == 1 for s in scores)
        
        if has_pos and has_neg:
            main_emotion = "Mixed"
            main_emoji = "🔀"
            main_icon = "mixed.png"
        else:
            main_emotion = "Mostly Neutral"
            main_emoji = "😐"
            main_icon = "neutral.png"

    #aggregate texts into a timeline format
    combined_reason = ""
    combined_thought = ""
    all_text_for_context = ""
    
    # Limit detailed timeline for longer periods to avoid huge text blocks
    display_logs = logs if len(logs) < 20 else logs[-20:] # Show last 20 entries max
    
    for log in display_logs:
        # Format timestamp based on period
        time_str = log['timestamp'][5:16] # MM-DD HH:MM
        emo = log['emotion_name']
        
        if log['note']:
            combined_reason += f"• {time_str} ({emo}): {log['note']}\n"
        if log['thought']:
            combined_thought += f"• {time_str} ({emo}): {log['thought']}\n"

    # Use ALL logs for context detection, not just the displayed ones
    all_text_for_context = " ".join([f"{l['note']} {l['thought']}" for l in logs])
    detected_contexts = detect_context(all_text_for_context)
    
    analysis = []
    suggestions = []
    
    #check for specific emotion spikes (e.g. Angry > 3)
    angry_count = emotions.count('Angry')
    if angry_count > 3:
        analysis.append(f"⚠️ Alert: You've logged 'Angry' {angry_count} times this {period_name}.")
        analysis.append("Frequent anger can indicate unmet needs or high stress levels.")
        suggestions.append("Consider physical exercise to release built-up tension.")

    if main_emotion == "Mixed":
        analysis.append(f"Your {period_name} was an emotional rollercoaster, shifting between highs and lows.")
        analysis.append("Fluctuations like this are normal during busy or eventful periods.")
        suggestions.append("Take a moment to decompress and process these events.")
    
    elif main_emotion == "Mostly Negative":
        analysis.append(f"It seems this {period_name} has been generally challenging for you (Avg Mood: Low).")
        suggestions.append("Be gentle with yourself; rest is important.")
    
    elif main_emotion == "Mostly Positive":
        analysis.append(f"You've had a generally positive {period_name} (Avg Mood: High)!")
        suggestions.append("Reflect on what went well so you can maintain this momentum.")
    
    else:
        analysis.append(f"Your {period_name} has been relatively stable and balanced.")

    #add context specific advice
    if "academic pressure" in detected_contexts or "work stress" in detected_contexts:
        analysis.append(f"Work or school pressure was a recurring theme this {period_name}.")
        suggestions.append("Schedule downtime to prevent burnout.")

    if "relationship issues" in detected_contexts:
        analysis.append(f"Social interactions played a big role in your {period_name}.")
        suggestions.append("Set boundaries if interactions feel draining.")

    if "fatigue" in detected_contexts:
        analysis.append("You mentioned being tired multiple times; you might be running on empty.")
        suggestions.append("Prioritize sleep and rest above all else.")

    if "financial stress" in detected_contexts or "financial general" in detected_contexts:
        suggestions.append("Focus on small, controllable financial steps.")

    if "health concerns" in detected_contexts:
        suggestions.append("Listen to your body and rest if needed.")

    if "social media negativity" in detected_contexts:
        suggestions.append("Consider a short digital detox.")

    #fallback suggestions if empty
    if not suggestions:
        if main_emotion == "Mostly Negative":
             suggestions.append("Try a quick breathing exercise (4-7-8 technique).")
        
        elif main_emotion == "Mixed":
             suggestions.append("Journaling might help untangle mixed feelings.")
        
        elif main_emotion == "Mostly Positive":
             suggestions.append("Share your positive energy with others.")
        else:
             suggestions.append("Practice mindfulness to maintain balance.")

    #remove duplicates while preserving order
    seen = set()
    suggestions = [x for x in suggestions if not (x in seen or seen.add(x))]

    #limit to 5 suggestions max
    suggestions = suggestions[:5]

    return {
        "emotion": main_emotion,
        "emoji": main_emoji,
        "icon": main_icon,
        "causes": analysis,
        "suggestions": suggestions,
        "encouragement": get_encouragement("neutral", detected_contexts),
        "reflection": {
            "reason": combined_reason.strip() if combined_reason else f"No specific situations recorded this {period_name}.",
            "thought": combined_thought.strip() if combined_thought else f"No specific thoughts recorded this {period_name}."
        }
    }

@ai_feedback_bp.route("/ai_feedback")
@ai_feedback_bp.route("/ai_feedback/<int:log_id>")
def ai_feedback(log_id=None):
    username = session.get("username")
    if not username:
        return redirect("/login")
    
    from .logemotion import get_emotion_styling
    
    log = None
    
    #data containers
    single_data = None
    daily_data = None
    weekly_data = None
    monthly_data = None
    selected_date_str = None
    selected_month_str = None
    selected_week_str = None
    view_type = 'dashboard' #default to dashboard view

    if log_id:
        #specific log selected
        log = get_emolog_by_id(log_id)
        if log and log['username'] != username:
            flash("You do not have permission to view this log.", "error")
            return redirect(url_for('home.dashboard'))
        
        view_type = 'single'

    if not log_id:
        #when no log's selected, show data for daily/weekly/monthly
        all_logs = UserManager.get_emotion_logs(username)
        now = datetime.now()
        
        #daily logs
        date_param = request.args.get('date')
        target_date = now
        if date_param:
            try:
                target_date = datetime.strptime(date_param, '%Y-%m-%d')
            except ValueError:
                pass
        
        selected_date_str = target_date.strftime('%Y-%m-%d')
        
        todays_logs = [l for l in all_logs if l['timestamp'].startswith(selected_date_str)]
        if todays_logs:
            daily_data = generate_aggregated_feedback(todays_logs, "day")
            daily_data['timestamp'] = f"Daily Summary - {selected_date_str}"

        #weekly logs
        week_param = request.args.get('week')
        
        if week_param:
            selected_week_str = week_param
            try:
                y, w = map(int, week_param.split('-W'))
                week_start = datetime.fromisocalendar(y, w, 1)
                week_end = week_start + timedelta(days=7)
                week_label = f"Week {week_param}"
            except (ValueError, AttributeError):
                week_start = now - timedelta(days=7)
                week_end = now + timedelta(days=1) # Future buffer
                week_label = "Last 7 Days"
        else:
            #default last 7 days
            week_start = now - timedelta(days=7)
            week_end = now + timedelta(days=1)
            week_label = "Last 7 Days"
            #for website the week format is shown correctly when user is trying to pick a week
            isocal = now.isocalendar()
            selected_week_str = f"{isocal.year}-W{isocal.week:02d}"

        weekly_logs = []
        for l in all_logs:
            l_date = datetime.strptime(l['timestamp'], "%Y-%m-%d %H:%M:%S")
            if week_start <= l_date < week_end:
                weekly_logs.append(l)
        
        if weekly_logs:
            weekly_data = generate_aggregated_feedback(weekly_logs, "week")
            weekly_data['timestamp'] = f"{week_label} Summary"

        #monthly logs
        month_param = request.args.get('month')
        if month_param:
            selected_month_str = month_param
        else:
            selected_month_str = now.strftime('%Y-%m')
            
        monthly_logs = [l for l in all_logs if l['timestamp'].startswith(selected_month_str)]
        if monthly_logs:
            monthly_data = generate_aggregated_feedback(monthly_logs, "month")
            dt_m = datetime.strptime(selected_month_str, '%Y-%m')
            monthly_data['timestamp'] = f"Monthly Summary - {dt_m.strftime('%B %Y')}"
        
    #if no data to show
    if not log and not daily_data and not weekly_data and not monthly_data: 
        return render_template("ai_feedback.html", empty=True)
    
    #determine active tab when user requests(aka clicking the tab)
    active_tab = 'daily'
    if request.args.get('month'):
        active_tab = 'monthly'
    elif request.args.get('week'):
        active_tab = 'weekly'

    if log:
        log_data = dict(log)

        #load saved feedback from db first
        full = None
        if log_data.get("ai_full_feedback"):
            try:
                full = ast.literal_eval(log_data["ai_full_feedback"])
            except (ValueError, SyntaxError):
                full = None

        # 2. Check for STALE DATA
        if full:
            stored_emo = full.get("emotion", "").lower()
            current_emo = log_data["emotion_name"].lower()
            
            stored_reason = (full.get("reflection", {}).get("reason") or "").strip()
            current_reason = (log_data.get("note") or "").strip()
            
            stored_thought = (full.get("reflection", {}).get("thought") or "").strip()
            current_thought = (log_data.get("thought") or "").strip()

            if (stored_emo != current_emo) or (stored_reason != current_reason) or (stored_thought != current_thought):
                full = None 

        if not full:
            full = generate_full_feedback(
                log_data["emotion_name"],
                log_data["note"] or "",
                log_data.get("thought", "")
            )
        
        style = get_emotion_styling(log_data["emotion_name"])
        emotion_display = log_data["emotion_name"]
        
        # Package single data
        single_data = full
        single_data['emotion'] = emotion_display
        single_data['emoji'] = style["emoji"]
        single_data['icon'] = style.get("icon")
        single_data['timestamp'] = log_data.get("timestamp")

    return render_template(
        "ai_feedback.html",
        view_type=view_type,
        single_data=single_data,
        daily_data=daily_data,
        weekly_data=weekly_data,
        monthly_data=monthly_data,
        log_id=log_id,
        selected_date=selected_date_str,
        selected_month=selected_month_str,
        selected_week=selected_week_str,
        active_tab=active_tab,
        empty=False
    )