from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from .users import UserManager
import ast
import random
from datetime import datetime, timedelta
from collections import Counter
from Databases.emologdb import get_emolog_by_id
import re

ai_feedback_bp = Blueprint('ai_feedback', __name__)

#general positive and negative word lists
POSITIVE_WORDS = ["happy", "good", "great", "excited", "love", "wonderful", "amazing", "best", "fun", "joy",
                  "blessed", "lucky", "not bad", "fanstastic", "awesome", "pleased", "satisfied", "grateful",
                  "cheerful", "elated", "overjoyed", "thrilled", "delighted", "joyful", "radiant", "lighthearted",
                  "proud", "relief", "relieved", "confident", "content", "calm", "peaceful", "better", "improving",
                  "progress", "productive", "cute", "sweet", "fun", "laugh", "smile", "smiling", "joke", "humor", "humorous",
                  "pass", "passed", "safe", "secure", "hope", "hopeful", "optimistic", "eager", "energetic", "strong",
                  "healthy", "fit", "beautiful", "smart", "easy", "smooth", "fresh", "clean", "free", "freedom", "like",
                  "likes"]
NEGATIVE_WORDS = ["unhappy", "sad", "angry", "stressed", "anxious", "bad", "terrible", "awful", "hate", "frustrated",
                  "lonely", "pain", "sick", "cry", "not good", "aint good", "ain't good", "fail", "failed", "failing",
                  "loss", "lost", "losing", "missed", "missing", "worst", "horrible", "disaster", "mess", "hard",
                  "difficult", "tough", "struggle", "struggling", "stuck", "trapped", "boring", "bored", "annoyed",
                  "irritated", "mad", "furious", "scared", "afraid", "fear", "terrified", "nervous", "uneasy",
                  "dread", "panic", "guilt", "guilty", "shame", "ashamed", "embarrassed", "regret", "jealous", "envy",
                  "tired", "exhausted", "drained", "weak", "hurt", "hurting", "broken", "damaged", "stupid", "useless",
                  "hopeless", "worthless", "pointless", "troubled", "sucks", "hate", "hates", "hating", ]

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
            "busy", "productive", "errands", "cleaning", "cooking", "routine", "planning", 
            "journaling", "laundry", "organized", "chores", "housework", "busying", "chore",
            "errands"
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
            "swim", "yoga", "pilates", "football", "basketball", "badminton", "hiking", "swimming", 
            "volleyball", "cycling", "bike ride", "marathon", "triathlon", "stretching", "dance",
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
        "relationship general": [
            "friend", "family", "partner", "parents", "roommate", "housemate", "peer", "social", 
            "socialize", "classmate", "colleague", "coworker", "neighbor", "meet up", "hang out", "bf", 
            "boyfriend", "girlfriend", "husband", "wife", "mom", "dad", "mother", "father", "sister", 
            "brother", "sibling", "cousin", "gf", "significant other", "mate", "pal", "buddy",
            "date", "dating"
        ],
        "relationship issues": [
            "argument", "fight", "conflict", "breakup", "toxic", "ghosted", "drama", "gossip", 
            "red flag", "reject", "dumped", "cheated", "ex", "tea", "ick", "betray", "jealous", 
            "envy", "divorce", "gaslight", "love bomb", "clingy", "distant", "misunderstanding", 
            "codependent", "third wheel", "friendzone", "catfish", "lie", 
            "envies", "gossiping", "gossipping", "envying"
        ],
        "relationship positive": [
            "bestie", "bff", "best friend", "squad", "love", "date", "dating", "marriage", 
            "compromise", "apologize", "forgive", "trust", "support", "caring", "quality time", "crush", 
            "deep talk", "vibe", "wholesome", "grateful for them", "soft launch"
        ],
        "self-esteem issues":[
            "ugly", "fat", "stupid", "hate myself", "useless", "failure", "worthless", "cringe",
            "awkward", "insecure", "imposter", "disappointment", "compare", "loser", "dumb",
            "mistake", "guilt", "shame", "embarrassed", "body image", "skinny", "acne", "looks",
            "appearance", "unlovable", "not enough", "mid", "basic", "try hard", "people pleaser"
        ],
        "self-esteem positive":[
            "confidence", "validation", "glow up", "proud of myself", "self-love", "worthy", "enough",
            "accepting", "confident", "great about myself", "good about myself"
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
            "subscribe", "post", "upload", "story", "status", "app", "comment", "stream", "posted",
            "streams", "feeds", "uploads", "uploading", "uploaded", "commented", "notifications",
            "messaged", "messaging", "subscribes", "subscribed", "scrolls"
        ],
        "social media negativity": [
            "bully", "toxic", "fake", "drama", "unfollow", "cancel", "troll", "hater", 
            "block", "unfollow", "cyberbully", "death threat", "expose", "clout", "flop", "shade", "snub",
            "death threats", "unfollows", "haters", "cyberbulling", "cyberbullies", "cancel culture",
            "sasaeng", "cancelled", "cancels"
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
            "rain", "hot", "sun", "weather", "storm", "humid", "cold", "gloom", "dark", "snow", "fog",
            "gloomy", "sky"
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
        for word in keywords:
            #\b ensures we match whole words only (stops 'app' in 'happy')
            #{word[-1]}* allows the last letter to repeat (catches 'exammm')
            pattern = rf"\b{word}{word[-1]}*\b"
            
            if re.search(pattern, text):
                detected.append(category)
                break  #move to the next category once a match is found          
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
            "A quiet mind is a creative mind. Use this balance wisely.",
            "It's okay to just 'be'. Not every day needs to be a rollercoaster.",
            "Sometimes a chill day is exactly what the soul needs.",
            "Embrace the stillness. You don't always have to be 'on'."
        ],
        "sad": [
            "This feeling is temporary, but your strength is permanent.",
            "It's okay not to be okay. Be gentle with yourself today.",
            "Stars can't shine without darkness. You will get through this.",
            "It's okay to rot in bed for a bit if you need to. Your feelings are valid.",
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
                return "It's good that you're noticing some relief. Staying calm while you navigate these symptoms is very effective."
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "Acknowledging the discomfort without letting it overwhelm you shows great mental strength."
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
                return "Recovery isn't always linear. Staying patient with your body's pace shows great resilience."
            return "It's good to feel steady and well. Maintaining your health is a rewarding habit."
        
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                "Despite you're frustrated about the discomforts from healing, you're still finding positivity!"
            return "It's normal to get frustrated during the healing process."

    elif "health general" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's impressive that you're maintaining a positive outlook while managing your health routines!"
            return "It's a great feeling to be proactive about your health and body. Keep up that positive energy!"
        
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great to see you're feeling steady and balanced while taking care of your physical well-being."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Handling medical appointments or routines can be a hassle, but stay focused on the goal of wellness."
            return "Staying on top of your health appointments and routines is a solid habit for long-term health."
        
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that even amidst health-related chores, you're still finding reasons to be grateful!"    
        return "Managing health matters can be a constant, sometimes draining task. You're doing the work to take care of yourself."

    elif "transport stress" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's impressive that you're staying positive despite the commute delays!"
            return "Even with transport hurdles, your positive energy is great to see. Safe travels!"
            
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "Despite having a level head towards transport stress, you still find positivity!"
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "Don't feel bad for having a neutral approach to transport stress; staying patient is a skill."
            return "Commuting issues are frustrating. Keeping a level head helps the time pass faster."
            
        else: 
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that even amidst a stressful commute, you still find reasons to be grateful!"
            return "Traffic and delays can be so draining. Take a deep breath and you'll get there eventually."

    elif "transport general" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "Although commuting can be a hassle, it's great you're maintaining a positive outlook!"
            return "Enjoy the journey! It's a great time to listen to some music or just enjoy the ride."
            
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great to see that you're feeling steady and balanced during your travels."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "It's valid to feel neutral while travelling, it must've been boring right?"
            return "Having a neutral approach to your daily commute is a good way to save your mental energy."
            
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                "Despite the frustrations while travelling, you still find positivity!"
            return "Traveling can be tiring. Remember to rest once you reach your destination."
        
    elif "relationship positive" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if "emotional release" in detected_contexts:
                return "Sharing your joy with loved ones amplifies the happiness. Those are beautiful tears of joy!"
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's impressive that you're focusing on the warmth of your relationships even when things feel heavy."
            return "It's wonderful to feel supported and connected. Cherish these wholesome bonds!"
        
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "Maintaining a calm and steady heart while being around those you trust is a sign of true security."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Even in wholesome relationships, it's okay to have slight negativity or neutral approach to how you feel."
            return "Emotions can be complex; feeling calm and neutral in the presence of loved ones is perfectly okay."

        else:
            if "emotional release" in detected_contexts:
                return "Crying or venting with people you trust is a healthy way to bond. It's okay to let your guard down."
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that you can still acknowledge the support around you, even when you're feeling down."
            return "It's okay to feel heavy even when you're around supportive people. Your feelings are always valid."
        

    elif "relationship issues" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that you're finding positivity and growth even amidst relationship challenges!"
            return "Maintaining your happiness despite interpersonal drama shows great emotional resilience."
        
        elif emotion == "neutral":
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "Taking a neutral, balanced approach toward a tough interaction shows great maturity and self-control."
            elif any(word in full_text for word in POSITIVE_WORDS):
                return "Processing relationship conflicts with a calm mind helps you see the situation more clearly."
            return "It's understandable to feel neutral after a tough interaction. Take the time you need to process it."
            
        else:
            if "emotional release" in detected_contexts:
                return "Letting those emotions out is the first step to feeling lighter. It's okay to cry over relationship hurt."
            if any(word in full_text for word in POSITIVE_WORDS):
                return "Even when things are toxic or difficult, finding small reasons to be grateful is a powerful strength."
            return "Relationship conflicts are draining. Protect your peace and remember that setting boundaries is healthy."

    elif "relationship general" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if "emotional release" in detected_contexts:
                return "It's wonderful to have tears of joy when spending time with the people in your life!"
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's great that you're staying positive even when your social interactions feel a bit complicated."
            return "Spending time with your social circle is a great way to boost your mood and stay connected."
        
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's okay to have mixed feelings about social plans; staying grounded is a solid way to handle the day."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Don't feel bad for taking a neutral approach to socializing; it's okay to just exist alongside others."
            return "Sometimes an ordinary day of social interaction is exactly what you need to feel balanced."
        
        else: 
            if "emotional release" in detected_contexts:
                return "Venting about social challenges is a healthy way to release built-up pressure from your day."
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that even amidst social fatigue, you still find small reasons to be grateful for your peers."
            return "It's normal for interactions with family or friends to be complicated. Give yourself space if you need it."

    elif "pet" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's wonderful that your pet is helping you stay positive even after a difficult day."
            return "Pets bring so much joy! Enjoy these sweet and happy moments with your furry friend."
            
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "There's a special kind of peace i n just existing alongside your pet. It's great to see you so content."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "When things feel boring or draining, the quiet presence of a pet can be the best kind of balance."
            return "Sometimes just sitting quietly with your pet is the best way to recharge your energy."
            
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that even when you're feeling down, your pet is there to provide some comfort and love."
            return "Pets are amazing listeners during tough times. Let their presence help you feel a little less alone today."
            
    elif "fitness" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in ["hobby", "hobbies", "passion"]):
                return "It's great to have such activity as your hobby/passion and having fun!"
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's impressive that you're pushing through the struggle and finding joy in staying active!"
            return "Great job on staying active! Those endorphins are clearly working their magic on your mood."
        
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "Staying grounded and consistent with your movement is a great way to maintain your inner balance."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Even when training feels like a chore, showing up for your body is a sign of true discipline."
            return "It's great that you're moving your body. Consistency is the key to long-term health."

        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that you're finding strength in movement even when you're not feeling your best."
            return "Exercise can be a release, but remember to listen to your body and rest if you're feeling drained."
    
    elif "hobbies" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's wonderful that your passions bring you joy even when things don't go perfectly."
            return "It's wonderful that your hobbies are bringing you joy! Keep indulging in the things you love."
        
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's satisfying to make steady progress in what you love. Enjoy that sense of calm accomplishment."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "It's okay to have a quiet or neutral approach to your hobbies; sometimes just 'doing' is enough."
            return "Engaging in activities you love is a solid way to keep your mind balanced and refreshed."
            
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that even when things are tough, you can still find a spark of joy in your interests."
            return "When life feels heavy, your hobbies can be a safe space. Take your time to reconnect with what you love."

    elif "daily hustle" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's impressive that you're staying positive and finding your flow despite the daily grind!"
            return "It's great to see you're finding joy and feeling productive in your daily routine!"

        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "Staying on top of your daily responsibilities with a calm mind is a very rewarding habit."
            
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Don't feel bad for having a neutral approach to chores or routines; staying disciplined is what counts."
            return "Managing your daily hustle with a steady hand helps keep your life in a healthy balance."

        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that even amidst the pressure of a busy day, you're still finding small reasons to be grateful."
            return "The daily grind can be overwhelming. Remember to pause, take a deep breath, and care for yourself today."
        
    elif "emotional release" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's completely valid to let those tears out; releasing the tension of the journey makes the joy even sweeter."
            return "It's wonderful to have tears of joy! Letting those happy emotions flow is a beautiful way to celebrate."
        
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "Releasing that built-up energy with a calm mind is a powerful way to reset and find your balance again."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Sometimes the body needs to vent or cry even when the mind feels quiet. Trust the process of letting it out."
            return "Crying or venting is a natural way to process your experiences. Give yourself the space to feel lighter."

        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's brave to let your guard down and release those feelings while still holding onto a spark of hope."
            return "Letting it all out is a healthy and necessary release. You don't have to carry the weight of these emotions alone."
    
    elif "loneliness" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's impressive how you've turned this moment into a positive experience for yourself despite you don't actually feel great."
            return "It's great that you're finding joy in your own company! Embracing solitude is a wonderful strength."
            
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "There is a peaceful strength in being comfortable with yourself. Enjoy this steady, quiet time."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "When the silence feels a bit heavy, remember that it's okay to just 'be' without needing to feel any particular way."
            return "It's okay to feel neutral when you're by yourself. Solitude can be a helpful time to recharge."
            
        else:
            if any(word in full_text for word in ["cry", "tears", "vent", "sob"]):
                return "Letting those feelings out is a natural way to cope with isolation. You don't have to be strong all the time."
            if any(word in full_text for word in POSITIVE_WORDS):
                return "Even when you feel unseen, it's brave to hold onto those sparks of gratitude."
            return "Feeling lonely can be heavy. Please remember that your presence matters, and it's okay to reach out when you're ready."
    
    elif "social media negativity" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in ["envy", "envies", "envying", "jealous"] + NEGATIVE_WORDS):
                return "It's impressive that you're staying positive and rising above the drama even when social media feels toxic!"
            return "It's great that you're maintaining such a high vibe despite the negative experiences you've encountered online."
            
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "Processing social media conflict with a calm mind helps you stay in control of your digital well-being."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Don't feel bad for taking a detached, neutral approach to online negativity; it's a very mature way to protect your peace."
            return "It's understandable to feel neutral after encountering negativity online. Staying objective is a solid habit."
            
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that even amidst social media shade or drama, you're still finding small reasons to be grateful."
            return "Negative experiences on social media can be really draining. Remember that your worth isn't defined by what happens on a screen."
    
    elif "social media general" in detected_contexts:
        if emotion in ["happy", "excited"]:
            return "It's wonderful to feel connected! Those notifications and messages can really brighten a day."
        
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great to see you managing your digital notifications and screen time with such balance."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Scrolling through your feed with a neutral mind is a good way to avoid digital fatigue."
            return "Routine digital activity is part of the day. Remember to give your eyes a break from the screen occasionally."
            
        else: 
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's impressive that you still find positivity despite being overhwhelmed by social media."
            return "Being constantly connected can be overwhelming. Don't feel pressured to reply to every message right away."
    
    elif "social media platform" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "Even when the feed is a mess, it's great that you're finding enjoyment in your favorite apps!"
            return "It's great that you're enjoying your time exploring these platforms! Enjoy the content."
        
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's good to feel balanced while browsing. Mindful use is the best way to enjoy social media."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "It's okay to feel neutral even when the algorithm is repetitive; don't feel bad for just scrolling along."
            return "Mindful browsing is a solid habit. Just keep checking in with yourself as you go."
            
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's impressive that you still find positivity despite being overhwhelmed by social media platforms."
            return "If your time on these apps is feeling heavy, remember it's okay to log off and reset for a bit."
    
    elif "weather" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's impressive that you're maintaining a sunny outlook regardless of the weather outside!"
            return "It's great that the weather is adding to your positive energy today. Enjoy the atmosphere!"
            
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's nice to feel balanced and steady, no matter what the weather is doing outside."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Don't feel bad for feeling a bit flat when the weather is gloomy; your mood can naturally follow the environment."
            return "The weather often sets the pace for the day. Take this calm moment to just exist in the present."
            
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that even on a dark or stormy day, you're still finding reasons to be grateful."
            return "The weather can really affect our energy. Remember to be gentle with yourself if the gloom is feeling heavy."
    
    elif "uncertainty" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's impressive that you're embracing the unknown with such a hopeful and positive spirit!"
            return "It's wonderful to feel excited about your dreams and the direction your life is heading."
            
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "Taking a steady, objective look at your future plans is a very mature way to find your direction."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Don't feel bad for having a neutral approach toward uncertainty; processing your choices takes time."
            return "Navigating the unknown with a calm head helps you make the best decisions for your future."
            
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that even amidst worries about the future, you're still finding a spark of hope."
            return "Adulting and future plans can be overwhelming. Remember, it's okay not to have all the answers right now."
        
    elif "fatigue" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's impressive that you're staying so positive even when your energy is running low!"
            return "It's great that you're feeling energized! Just make sure to rest later so you don't burn out."
            
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's good to see you're feeling balanced; giving your body a moment to rest is a smart move."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Don't feel bad for having a neutral approach to your fatigue; sometimes you just need to power through."
            return "When you're feeling lethargic, taking things one step at a time is the best way to manage your day."
            
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that even amidst the burnout, you're still finding a sense of accomplishment."
            return "Burnout and exhaustion are signs that your body needs a real break. Please prioritize your rest today."
        
    elif "self-esteem positive" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "You've worked hard to build this confidence; despite there were some struggles during the journey."
            return "That confidence looks great on you! Enjoy this feeling of being truly comfortable in your own skin."
            
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's good to have a quiet, steady sense of confidence in your abilities while you go about your day."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "Holding onto your sense of worth even when you're feeling flat or tired is a sign of solid self-assurance."
            return "Maintaining a steady sense of self-confidence is a powerful habit for long-term peace of mind."
            
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's brave to acknowledge your worth even on days when your emotions feel a bit heavy."
            return "Even on the hard days, remembering your value is a huge strength. This feeling will pass, but your worth remains."
        
    elif "self-esteem issues" in detected_contexts:
        if emotion in ["happy", "excited"]:
            if any(word in full_text for word in NEGATIVE_WORDS):
                return "It's impressive that you're maintaining a positive outlook even when facing those inner insecurities."
            return "It's great that you're feeling good! Don't let those old insecurities hold back your current happiness."
            
        elif emotion == "neutral":
            if any(word in full_text for word in POSITIVE_WORDS):
                return "Noticing your mistakes without letting them shift your mood shows a very practical and steady mindset."
            elif any(word in full_text for word in NEGATIVE_WORDS):
                return "It's okay to have days where you feel ordinary or critical of yourself. Staying objective is just part of the process."
            return "Embracing a calm, non-judgmental view of yourself is a powerful way to find inner peace."
            
        else:
            if any(word in full_text for word in POSITIVE_WORDS):
                return "It's great that even when you're being hard on yourself, you can still find a reason to be proud of your effort."
            return "You are much more than your mistakes or your appearance. Please be gentle with yourself today."
   
    #if none of the keywords matched, it goes for general emotion based on constant +ve or -ve feedback
    if emotion in ["happy", "excited"]: 
        if any(word in full_text for word in NEGATIVE_WORDS):
            return "It seems you're feeling positive, but your notes mention some challenges. It's okay to have mixed feelings."
        if any(word in full_text for word in POSITIVE_WORDS):
            return "It seems you're feeling positive, glad to see you are feeling great!"

    if emotion in ["sad", "angry", "stressed", "anxious"]:
        if any(word in full_text for word in POSITIVE_WORDS):
            return "It seems you're feeling down, but your notes mention some positives. It's okay to have mixed feelings."
        if any(word in full_text for word in NEGATIVE_WORDS):
            return "It seems you're feeling down, take a deep breath."

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
            if "pet" in reason_contexts:
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
            
            elif "self-esteem issues" in reason_contexts:
                analysis.append("Setting expections too high on yourself can cause frustrations and stress.")
            
            elif "fitness" in reason_contexts:
                analysis.append("Pushing your body too hard without enough recovery can lead to physical and mental stress.")
            
            elif "health issues" in reason_contexts:
                analysis.append("Physical discomfort or illness is a major stressor on the mind and body.")
            
            elif "health positive" in reason_contexts:
                analysis.append("Negative emotions can delay the process of healing, so turn that frown upside down.")

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
            
            elif "social media general" in reason_contexts:
                analysis.append("High engagement on social media can lead to information overload, contributing to stress.")

            elif "social media platform" in reason_contexts:
                analysis.append("Spending extended time on social media platforms can sometimes increase stress levels due to constant connectivity and exposure to various content.")
            
            elif "financial general" in reason_contexts:
                analysis.append("Managing finances seems to be a source of pressure right now.")
            
            elif "financial stress" in reason_contexts:
                analysis.append("Worries about money can be a heavy burden, contributing significantly to stress.")
            
            elif "daily hustle" in reason_contexts:
                analysis.append("The accumulation of routine micro-tasks appears to be causing 'cognitive load'—where the mind feels cluttered by unfinished business.")
            
            elif "technology" in reason_contexts:
                analysis.append("Digital stressors often lead to 'technostress,' a state of exhaustion caused by an inability to mentally disconnect from digital tools.")

            elif "social media positive" in reason_contexts:
                analysis.append("Positive social feedback can paradoxically trigger anxiety through 'upward social comparison' or the pressure to sustain a certain digital persona.")

            elif "fatigue" in reason_contexts:
                analysis.append("Physical exhaustion is likely lowering your emotional regulation threshold, making standard challenges feel significantly more threatening.")

            elif "weather" in reason_contexts:
                analysis.append("Environmental stressors, such as extreme heat or low light, are known to impact serotonin levels, intensifying an internal sense of unease.")

            elif "health positive" in reason_contexts:
                analysis.append("The transition period of recovery can cause 'healing anxiety,' where the fear of relapse or the pace of improvement creates mental strain.")

            elif "transport general" in reason_contexts:
                analysis.append("Commuting involves 'passive stress'—a feeling of powerlessness caused by being in a high-stakes environment (travel) with zero control over variables.")
            
        if thought:
            if "uncertainty" in thought_contexts:
                analysis.append("Your thoughts are focused on the unknown, which fuels anxiety.")
            
            if "self-esteem issues" in thought_contexts:
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

        if "social media general" in reason_contexts:
            suggestions.append("Set your phone to 'Do Not Disturb' for the next 30 minutes to reduce sensory input.")

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

            elif "emotional release" in reason_contexts:
                analysis.append("Crying is often a necessary release valve for overwhelming feelings; it helps reset your nervous system.")
            
            elif "social media negativity" in reason_contexts:
                analysis.append("Negative interactions on social media can contribute to feelings of sadness and isolation.")

            elif "social media general" in reason_contexts:
                analysis.append("Over-engagement with social media can lead to feelings of inadequacy or sadness due to constant comparisons.")

            elif "social media platform" in reason_contexts:
                analysis.append("Spending too much time on social media platforms can sometimes lead to feelings of sadness due to exposure to negative contents.")
            
            elif "fitness" in reason_contexts:
                analysis.append("Lack of physical activity can contribute to feelings of sadness due to lower endorphin levels.")
            
            elif "daily hustle" in reason_contexts:
                analysis.append("The 'daily grind' of routine chores can lead to emotional stagnation, where a lack of variety creates a persistent low mood.")

            elif "technology" in reason_contexts:
                analysis.append("Digital fatigue or a sense of disconnection despite being 'online' can contribute to a subtle, modern form of melancholy.")

            elif "fatigue" in reason_contexts:
                analysis.append("Physical depletion often mimics sadness; when the body is exhausted, the brain struggle to maintain emotional resilience.")

            elif "weather" in reason_contexts:
                analysis.append("Environmental factors like a lack of sunlight or gloomy conditions can physically lower serotonin levels, triggering a 'seasonal' low.")

            elif "uncertainty" in reason_contexts:
                analysis.append("A lack of clarity regarding future goals can lead to 'anticipatory grief,' where the mind mourns a lost sense of security.")

            elif "self-esteem positive" in reason_contexts:
                analysis.append("Paradoxically, moments of self-reflection after a 'glow up' or success can stir up old insecurities, leading to a temporary emotional dip.")

            elif "social media positive" in reason_contexts:
                analysis.append("The pressure to maintain a successful digital image or keep up with viral trends can be an exhausting and lonely experience.")

            elif "financial gain" in reason_contexts:
                analysis.append("Unexpected financial changes, even positive ones, can cause 'adjustment sadness' as you navigate new responsibilities or lifestyle shifts.")

            elif "transport general" in reason_contexts:
                analysis.append("The monotony of commuting can trigger a sense of 'transit loneliness,' making you feel isolated despite being in a public space.")

            elif "health positive" in reason_contexts:
                analysis.append("Post-recovery periods can sometimes feel empty, as the focus shifts from the goal of 'getting well' back to the weight of daily life.")
            
            if not reason_contexts:
                analysis.append("Sometimes specific events trigger sadness because they touch on deeper values or needs.")

        if thought:
            if "self-esteem issues" in thought_contexts:
                analysis.append("Your internal monologue seems critical of yourself, which deepens the sadness.")
            
            elif "emotional release" in thought_contexts:
                analysis.append("Thinking about crying indicates you are reaching a point of emotional overflow.")
            
            elif "loneliness" in thought_contexts:
                analysis.append("You are telling yourself that you are alone, but this feeling is temporary.")
   
            if not any(ctx in thought_contexts for ctx in ["uncertainty", "self-esteem issues"]):
                analysis.append("Your thoughts suggest self-doubt or emotional disappointment.")

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
            
            elif "daily hustle" in reason_contexts:
                analysis.append("Finding satisfaction in routine indicates high 'autonomy'—the psychological state of feeling in control of your daily environment.")
            
            elif "technology" in reason_contexts:
                analysis.append("A positive tech experience reflects 'frictionless interaction,' where the tool disappears and allows for a state of cognitive flow.")

            elif "social media positive" in reason_contexts:
                analysis.append("Positive digital engagement triggers the 'social reward' pathway, reinforcing a sense of community and belonging through digital mirroring.")

            elif "uncertainty" in reason_contexts:
                analysis.append("Happiness despite uncertainty suggests 'cognitive flexibility,' where the mind prioritizes current potential over the need for absolute control.")

            elif "fatigue" in reason_contexts:
                analysis.append("This suggests a state of 'eustress' or meaningful exhaustion, where the sense of purpose behind the fatigue outweighs the physical cost.")

            elif "achievement success" in reason_contexts:
                analysis.append("This emotional peak is a result of 'self-efficacy'—the rewarding realization that your personal actions have led to a desired outcome.")

            elif "academic pressure" in reason_contexts:
                analysis.append("Finding joy in studies indicates 'intrinsic motivation,' where the act of learning itself is providing the reward rather than just the final grade.")

            elif "self-esteem positive" in reason_contexts:
                analysis.append("Internal validation indicates that your current actions are highly aligned with your self-concept and personal values.")

            elif "health positive" in reason_contexts:
                analysis.append("Physical vitality provides a 'somatic foundation' for happiness, as the body communicates a state of safety and optimal functioning to the brain.")

            elif "work stress" in reason_contexts:
                analysis.append("Happiness amidst work stress shows 'resilience-based detachment,' where you are successfully separating your personal joy from professional pressure.")

            elif "financial gain" in reason_contexts:
                analysis.append("Financial developments contribute to 'safety-security satisfaction,' reducing the background noise of survival-based anxiety.")

            elif "relationship positive" in reason_contexts:
                analysis.append("Social joy is driven by 'interpersonal synchrony,' where high-quality connections act as a primary regulator for emotional stability.")

            if not reason_contexts:
                analysis.append("Identifying these personal sources of happiness helps you build resilience.")

        if thought:
            if "self-esteem" in thought_contexts:
                analysis.append("Your thoughts reflect a healthy sense of self-worth right now.")
            
            elif "achievement success" in thought_contexts:
                analysis.append("Reflecting on wins creates 'psychological momentum,' increasing the likelihood of approaching future tasks with confidence.")
            
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
            
            elif "uncertainty" in reason_contexts:
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
            
            elif "daily hustle" in reason_contexts:
                analysis.append("Enthusiasm for routine suggests a state of 'functional momentum,' where the efficiency of your daily cycle is providing its own reward.")
            
            elif "technology" in reason_contexts:
                analysis.append("This excitement suggests 'technological empowerment'—a boost in self-efficacy when tools effectively expand your capabilities.")

            elif "social media general" in reason_contexts:
                analysis.append("High engagement with digital feeds can trigger 'variable ratio rewards,' creating a cycle of excitement through constant novelty.")

            elif "technical difficulties" in reason_contexts:
                analysis.append("Feeling excited despite technical hurdles indicates 'resilience-based engagement,' where the problem-solving process itself has become rewarding.")

            elif "fatigue" in reason_contexts:
                analysis.append("Excitement during physical exhaustion often signals 'second wind' neurochemistry, where adrenaline temporarily overrides your need for recovery.")

            elif "weather" in reason_contexts:
                analysis.append("Atmospheric shifts can trigger 'environmental arousal,' where specific sensory conditions (like sunlight or a storm) stimulate your nervous system.")

            elif "self-esteem positive" in reason_contexts:
                analysis.append("This indicates an 'upward self-concept shift,' where your internal perception of worth is actively being reinforced by your current experiences.")

            elif "health positive" in reason_contexts:
                analysis.append("Biological vitality provides a 'somatic high,' as the body signals a state of peak physical readiness to the brain.")

            elif "work stress" in reason_contexts:
                analysis.append("Excitement under professional pressure suggests 'stress-is-enhancing' mindset, where you are successfully converting high stakes into fuel.")

            elif "financial stress" in reason_contexts:
                analysis.append("Maintaining enthusiasm despite money worries shows 'cognitive reappraisal,' where you are prioritizing non-monetary goals or growth.")

            elif "transport stress" in reason_contexts:
                analysis.append("Staying excited through travel delays indicates a high 'internal locus of control,' as you maintain your mood independently of external disruptions.")

            elif "emotional release" in reason_contexts:
                analysis.append("Enthusiasm following an emotional release indicates a successful 'post-cathartic reset,' clearing the path for high-energy optimism.")
            
            if not reason_contexts:
                analysis.append("Passion for specific interests is a great fuel for mental well-being.")
        
        if thought:
            if "emotional release" in thought_contexts:
                analysis.append("Your excitement is so strong it feels overwhelming; remember to breathe and stay grounded.")
            
            elif "self-esteem positive" in thought_contexts:
                analysis.append("Your internal monologue is currently facilitating a 'virtuous cycle,' where positive self-thoughts further amplify your energy levels.")
            
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
            
            elif "daily hustle" in reason_contexts:
                analysis.append("Engagement in routine tasks with a neutral affect suggests 'habitual efficiency,' where your actions are automated and mentally non-taxing.")
            
            elif "technology" in reason_contexts:
                analysis.append("A neutral tech experience indicates 'functional transparency,' where tools are working as intended without creating cognitive friction.")

            elif "social media positive" in reason_contexts:
                analysis.append("This suggests 'digital stoicism'—the ability to acknowledge positive online feedback without becoming dependent on the dopaminergic hit.")

            elif "hobbies" in reason_contexts:
                analysis.append("Neutrality during leisure activities indicates 'passive recovery,' where you are engaging in a hobby purely for mental decompression rather than excitement.")

            elif "financial gain" in reason_contexts:
                analysis.append("Responding to financial developments neutrally indicates a high level of 'monetary stability' and a lack of survival-based emotional triggers.")

            elif "financial stress" in reason_contexts:
                analysis.append("Observing financial pressure neutrally suggests 'pragmatic detachment,' focusing on logical problem-solving rather than the anxiety of the debt.")

            elif "weather" in reason_contexts:
                analysis.append("Environmental neutrality shows 'climatic adaptation,' where your internal mood is stable enough to remain unaffected by external shifts in conditions.")

            elif "self-esteem positive" in reason_contexts:
                analysis.append("This indicates 'secure self-concept'—a state where your worth is a quiet, accepted fact that doesn't require active excitement or validation.")

            elif "health positive" in reason_contexts:
                analysis.append("Feeling neutral during health recovery suggests 'biological recalibration,' as the body returns to its standard state of well-being.")

            elif "work general" in reason_contexts:
                analysis.append("Professional neutrality often stems from 'work-life integration,' where tasks are viewed as standard responsibilities rather than emotional events.")

            elif "work stress" in reason_contexts:
                analysis.append("Maintaining neutrality under work pressure indicates 'professional resilience,' successfully insulating your inner state from workplace demands.")

            elif "transport general" in reason_contexts:
                analysis.append("A neutral commute indicates 'transit mindfulness,' where the act of traveling is treated as a transitional space for quiet thought.")

            elif "emotional release" in reason_contexts:
                analysis.append("Neutrality following an emotional release indicates the 'post-cathartic plateau,' where the system has successfully exhausted intense signals and reset.")
            
            if not reason_contexts:
                 analysis.append("Taking a step back to view things neutrally is a valuable skill.")

        if thought:
            if "uncertainty" in thought_contexts:
                analysis.append("You're observing the future without immediate fear, which is a very high level of mindfulness.")
            
            elif "self-esteem" in thought_contexts:
                analysis.append("You are viewing yourself and your progress realistically today, without being too hard on yourself.")    
            
            elif "fatigue" in thought_contexts:
                analysis.append("Your thoughts on exhaustion are being processed with 'somatosensory awareness,' recognizing physical needs without emotional judgment.")
        
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

            elif "technology" in reason_contexts:
                analysis.append("Frustration with technology often stems from 'agency disruption'—where a tool designed to empower you instead creates a barrier to your goals.")
            
            elif "social media positive" in reason_contexts:
                analysis.append("Anger in a positive digital context can indicate 'performative exhaustion,' where the pressure to maintain a certain image feels restrictive.")

            elif "hobbies" in reason_contexts:
                analysis.append("When passions trigger anger, it often reflects 'perfectionist friction,' where your current skill level or output isn't meeting your internal standards.")

            elif "fatigue" in reason_contexts:
                analysis.append("Physical depletion significantly lowers your 'irritability threshold,' causing the brain to interpret minor inconveniences as major threats.")

            elif "weather" in reason_contexts:
                analysis.append("Environmental factors like extreme heat can lead to 'thermal irritability,' a physiological state that primes the nervous system for aggressive responses.")

            elif "uncertainty" in reason_contexts:
                analysis.append("Anger toward the unknown is often a mask for 'existential powerlessness,' where the mind uses frustration to try and regain a sense of control.")

            elif "self-esteem positive" in reason_contexts:
                analysis.append("Anger following self-validation can be a defense against 'cognitive dissonance,' as you fight off old habits of self-doubt.")

            elif "health positive" in reason_contexts:
                analysis.append("Encountering anger during recovery may indicate 'restoration impatience,' where you are frustrated with the slow pace of physical healing.")

            elif "work general" in reason_contexts:
                analysis.append("Professional anger often signals a 'values misalignment,' where workplace demands or culture are clashing with your personal integrity.")

            elif "work stress" in reason_contexts:
                analysis.append("This suggests 'occupational burnout'—a state where chronic stress has depleted your patience and left you in a persistent state of high arousal.")

            elif "financial gain" in reason_contexts:
                analysis.append("Anger regarding financial wins can stem from 'unmet expectations' or the realization that a material gain hasn't solved a deeper emotional need.")

            elif "transport general" in reason_contexts:
                analysis.append("The monotony of travel can lead to 'transient frustration,' where the lack of stimulating progress makes you hyper-aware of minor irritants.")

            elif "transport stress" in reason_contexts:
                analysis.append("Traffic-induced anger is a classic example of 'thwarted goal-seeking,' where external factors out of your control are physically blocking your progress.")

            elif "achievement success" in reason_contexts:
                analysis.append("Anger after success may indicate 'achievement resentment,' perhaps because the win didn't feel as rewarding as you anticipated.")
            
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

    if "daily hustle" in detected_contexts:
        suggestions.append("Apply the '2-minute rule': if it takes less than 2 minutes, do it now")
        suggestions.append("Use a 'Done List' instead of a 'To-Do List' to visualize your productivity")

    if "technology" in detected_contexts:
        suggestions.append("Adjust your screen's blue light filter to reduce digital eye strain")
        suggestions.append("Organize your digital workspace and clear your desktop icons for clarity")

    if "social media platform" in detected_contexts or "social media general" in detected_contexts:
        suggestions.append("Turn off non-human notifications for 2 hours to reclaim your attention")
        suggestions.append("Practice 'mindful scrolling'—check in with how you feel every 10 minutes")

    if "social media positive" in detected_contexts:
        suggestions.append("Save your favorite positive comments or posts in a 'Joy' folder")
        suggestions.append("Log off while you're ahead to savor the good feelings without the dip")

    if "weather" in detected_contexts:
        suggestions.append("Adjust your environment (lighting or temperature) to balance out the external weather")
        suggestions.append("If it's sunny, try to get 10 minutes of natural light to boost serotonin")

    if "hobbies" in detected_contexts:
        suggestions.append("Dedicate even 15 minutes to your passion without worrying about the final result")
        suggestions.append("Try a 'parallel play' session—engage in your hobby while a friend does theirs")

    if "financial gain" in detected_contexts:
        suggestions.append("Put a small percentage of this gain into a 'future-you' savings pot")
        suggestions.append("Consider a small 'conscious splurge' that genuinely adds value to your life")

    if "transport general" in detected_contexts or "transport stress" in detected_contexts:
        suggestions.append("Use your commute time for an 'audio reset' with a favorite podcast or album")
        suggestions.append("Practice deep breathing or 'grip release' exercises while waiting in traffic")

    if "health positive" in detected_contexts:
        suggestions.append("Take note of how this vitality feels to remember it during future recoveries")
        suggestions.append("Maintain this momentum with one small, sustainable wellness habit today")

    if "emotional release" in detected_contexts:
        suggestions.append("Hydrate after crying; your body needs to replenish fluids after an intense release")
        suggestions.append("Take 5 minutes of absolute silence to let your nervous system fully reset")

    if "loneliness" in detected_contexts:
        suggestions.append("Visit a public space like a cafe or the MMU library to feel 'alone together'")
        suggestions.append("Write a letter or message to your future self about what you're learning right now")

    if "self-esteem positive" in detected_contexts:
        suggestions.append("Accept a compliment today without downplaying your own efforts")
        suggestions.append("Wear something that makes you feel confident to reinforce this internal state")

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
    analysis = [x for x in analysis if not (x in seen or seen.add(x))]

    #limit to 5 max for suggestions and analysis
    suggestions = suggestions[:5]
    analysis = analysis[:5]

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
    
    #limit detailed timeline for longer periods to avoid huge text blocks
    display_logs = logs if len(logs) < 20 else logs[-20:] #show last 20 entries max
    
    for log in display_logs:
        #timestamp format based on period
        time_str = log['timestamp'][5:16] #MM-DD HH:MM
        emo = log['emotion_name']
        
        if log['note']:
            combined_reason += f"• {time_str} ({emo}): {log['note']}\n"
        if log['thought']:
            combined_thought += f"• {time_str} ({emo}): {log['thought']}\n"

    #use ALL logs for context detection, not just the displayed ones
    all_text_for_context = " ".join([f"{l['note']} {l['thought']}" for l in logs])
    detected_contexts = detect_context(all_text_for_context)
    
    analysis = []
    suggestions = []
    
    #check for specific emotion spikes (e.g. angry > 3)
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
        suggestions.append("Schedule downtime to prevent burnout from academics or work.")

    if "relationship issues" in detected_contexts:
        analysis.append(f"Social interactions played a big role in your {period_name}.")
        suggestions.append("Set boundaries if interactions feel draining.")

    if "fatigue" in detected_contexts:
        analysis.append("You mentioned being tired multiple times; you might be running on empty.")
        suggestions.append("Prioritize sleep and rest above all else.")

    if "financial stress" in detected_contexts or "financial general" in detected_contexts:
        suggestions.append("Focus on small, controllable financial steps.")

    if "health issues" in detected_contexts:
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
    analysis = [x for x in analysis if not (x in seen or seen.add(x))]

    #limit to 5 max for suggestions and analysis
    suggestions = suggestions[:5]
    analysis = analysis[:5]

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

        #check for STALE DATA
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