from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from .users import UserManager
import ast
import random
from datetime import datetime, timedelta
from collections import Counter
from Databases.emologdb import get_emolog_by_id


ai_feedback_bp = Blueprint('ai_feedback', __name__)

# Global Constants for Word Detection
POSITIVE_WORDS = ["happy", "good", "great", "excited", "love", "wonderful", "amazing", "best", "fun", "joy", "blessed", "lucky"]
NEGATIVE_WORDS = ["unhappy", "sad", "angry", "stressed", "anxious", "bad", "terrible", "awful", "hate", "frustrated", "lonely", "pain", "sick", "cry"]

# Helper function to detect context from text
# NOTE: This is a simple substring search. It handles duplicates (e.g., "exammm") 
# but does not handle misspellings (e.g., "exan"). For more advanced matching,
# a fuzzy matching library like 'fuzzywuzzy' could be implemented.
def detect_context(text):
    text = text.lower()
    context_map = {
        "academic pressure": [
            "exam", "study", "assignment", "deadline", "test", "school", "grade", "gpa", "class",
            "quiz", "midterm", "final", "thesis", "fyp", "project", "presentation", "lecture", "tutorial",
            "lab", "semester", "submission", "due", "fail", "pass", "resit", "repeat", "transcript",
            "scholarship", "tuition", "fees", "enrollment", "coursework", "syllabus", "lecturer", "professor",
            "tutor", "dean", "campus", "university", "college", "uni", "degree", "diploma", "group project",
            "capstone", "internship", "practicum", "viva", "research", "paper", "essay",
            "procrastinate", "cramming", "burnout", "dropout", "academic validation", "study group", "library"
        ],
        "fatigue": [
            "tired", "sleep", "exhausted", "burnt out", "insomnia", "nap", "drained", "fatigue",
            "all-nighter", "sleepy", "zombie", "caffeine", "coffee", "energy drink", "no sleep", "awake",
            "burnout", "overworked", "collapse", "rest", "bed", "pillow", "woke up",
            "low energy", "lethargic", "dead", "dying", "comatose", "hibernating", "sluggish", "yawning", "snooze"
        ],
        "relationship issues": [
            "friend", "family", "partner", "argument", "fight", "conflict", "breakup", "toxic", "parents",
            "crush", "ghosted", "situationship", "roommate", "housemate", "drama", "gossip", "red flag", "bestie",
            "squad", "peer", "social", "reject", "dumped", "cheated", "ex", "boyfriend", "girlfriend", "bf", "gf",
            "tea", "ick", "trust", "lie", "betray", "jealous", "envy", "date", "dating", "marriage", "divorce",
            "gaslight", "love bomb", "boundaries", "clingy", "distant", "misunderstanding", "attachment style", 
            "codependent", "third wheel", "friendzone", "catfish", "talking stage", "soft launch", "lonely", "miss them", 
            "bff", "best friend", "love", "hate", "compromise", "apologize", "forgive"
        ],
        "health concerns": [
            "sick", "pain", "doctor", "ill", "headache", "hurt", "health", "body",
            "fever", "flu", "cold", "stomach", "migraine", "dizzy", "nausea", "vomit", "medicine", "pill",
            "period", "cramps", "injury", "broken", "bleed", "hospital", "clinic", "weight", "diet", "skin",
            "acne", "pimple", "hair"
        ],
        "work stress": [
            "job", "boss", "work", "salary", "meeting", "career", "colleague", "project",
            "internship", "part-time", "shift", "manager", "customer", "rude", "overtime", "ot", "client",
            "interview", "resume", "cv", "fired", "hired", "promotion", "raise", "colleague", "coworker",
            "office", "business",
            "micromanage", "toxic workplace", "kpi", "workload", "underpaid", "hustle", "grind", "corporate", 
            "9 to 5", "slack", "teams", "zoom fatigue", "commute", "unemployed", "job hunt"
        ],
        "financial": [
            "money", "cost", "expensive", "debt", "pay", "broke", "bill", "rent",
            "loan", "allowance", "budget", "save", "spend", "price", "cash", "wallet",
            "bank", "transfer", "shopping", "buy", "purchase", "afford", "cheap",
            "inflation", "groceries", "savings", "investment", "crypto", "stocks", "salary", "wage", 
            "poverty", "rich", "poor", "splurge", "treat myself", "retail therapy"
        ],
        "self-esteem": [
            "ugly", "fat", "stupid", "hate myself", "useless", "failure", "worthless", "confidence",
            "cringe", "awkward", "insecure", "imposter", "disappointment", "compare", "loser", "dumb", "flop",
            "mistake", "guilt", "shame", "embarrassed", "regret", "fault",
            "body image", "skinny", "acne", "looks", "appearance", "unlovable", "not enough", "validation",
            "glow up", "mid", "basic", "try hard", "people pleaser"
        ],
        "loneliness": [
            "lonely", "alone", "isolated", "nobody", "ignored", "miss",
            "left out", "excluded", "no friends", "homesick", "empty", "silence"
        ],
        "uncertainty": [
            "future", "career", "plans", "worried", "anxious", "what if", "unknown", "direction", "lost",
            "confused", "choice", "decision", "adulting", "graduation", "internship", "applications",
            "rejection", "waiting", "hopeful", "dream", "goal"
        ],
        "hobbies": [
            "game", "music", "read", "sport", "art", "draw", "code", "movie", "world of warcraft",
            "gaming", "valorant", "league", "netflix", "binge", "gym", "workout", "spotify", "concert",
            "travel", "food", "eat", "football", "basketball", "badminton", "hiking", "swim", "dance",
            "anime", "manga", "series", "cook", "bake", "write", "sing", "guitar", "piano", "shopping",
            "stream", "twitch", "youtube", "festival", "cafe", "coffee hopping", "thrifting", "fashion", 
            "makeup", "skincare", "pilates", "yoga", "meditation", "journaling", "podcast", "kpop", "kdrama",
            "podcast", "vlog", "photography", "blog", "diy", "craft", "knitting", "gardening", "poca", "photocard"
        ],
        "positive_events": [
            "party", "holiday", "vacation", "trip", "promotion", "date", "celebrate", "winning", "won", "success", "bonus", "award",
            "ace", "aced", "graduate", "convo", "internship", "offer", "hired", "vibe", "chill", "relax", "fun", "happy",
            "slay", "ate", "gift", "present", "surprise", "lucky", "blessed",
            "main character", "thriving", "healing", "productive", "accomplished", "proud", "grateful", "w", "win"
        ],
        "emotional_release": [
            "cry", "crying", "tears", "sob", "weep", "bawling", "break down", "teary",
            "scream", "yell", "vent", "rant", "explode", "meltdown"
        ],
        "social_media": [
            "instagram", "tiktok", "twitter", "x", "facebook", "snapchat", "story", "post", "like", "comment",
            "follower", "viral", "trend", "feed", "scroll", "screen", "phone", "notification", "dm", "message",
            "reply", "block", "unfollow", "xhs", "igtv", "live", "stream", "subscribe", "youtube",
            "doomscrolling", "fomo", "influencer", "reel", "algorithm", "screen time", "cyberbully", "troll",
            "cancel", "cancelled", "ratio", "clout", "aesthetic", "highlight reel", "netizens"
        ],
        "technology": [
            "wifi", "internet", "lag", "slow", "crash", "bug", "error", "laptop", "pc", "computer", "battery",
            "charge", "broken", "screen", "mouse", "keyboard", "software", "update", "blue screen", "frozen",
            "coding", "programming", "server", "hosting", "deploy", "git", "database", "backend", "frontend",
            "submission failed", "lost data", "corrupted", "loading", "ping"
        ],
        "transport": [
            "bus", "train", "mrt", "lrt", "grab", "taxi", "car", "drive", "traffic", "jam", "late", "wait",
            "parking", "road", "accident"
        ],
        "daily_hustle": [
            "busy", "productive", "errands", "cleaning", "cooking", "gym", "workout", "routine", "laundry",
            "grocery", "commute", "traffic", "driving", "walking", "parking", "planning", "organized",
            "journaling", "meditating", "hydration", "water"
        ],
        "achievement_success": [
            "won", "solved", "fixed", "completed", "finished", "accomplished", "award", "prize", "celebrate",
            "win", "victory", "success", "milestone", "breakthrough", "nailed it", "crushed it", "proud",
            "improvement", "progress", "growth", "finally", "done"
        ],
        "animal": [
            "dog", "cat", "pet", "puppy", "kitten", "animal", "fish", "bird", "hamster", "rabbit"
        ],
        "weather": [
            "rain", "hot", "sun", "weather", "storm", "wet", "humid", "cold", "gloom", "dark"
        ]
    }
    detected = []
    for category, keywords in context_map.items():
        if any(word in text for word in keywords):
            detected.append(category)
    return detected

def get_encouragement(emotion, contexts):
    """Returns a motivational message based on emotion."""
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
    
    # Default fallback
    options = messages.get(emotion, ["Trust the process. You are doing your best."])
    return random.choice(options)

def generate_short_feedback(emotion, reason="", thought=""):
    emotion = emotion.lower()
    # Combine text for analysis
    full_text = f"{reason} {thought}".lower()

    # --- Mixed Emotion Check ---
    # If a positive emotion is chosen but the text contains negative words, flag it.
    if emotion in ["happy", "excited"] and any(word in full_text for word in NEGATIVE_WORDS):
        return "It seems you're feeling positive, but your notes mention some challenges. It's okay to have mixed feelings."

    if emotion in ["sad", "angry", "stressed", "anxious"] and any(word in full_text for word in POSITIVE_WORDS):
        return "It seems you're feeling down, but your notes mention some positives. It's okay to have mixed feelings."

    if emotion == "neutral":
        if any(word in full_text for word in POSITIVE_WORDS):
             return "You're feeling neutral, but your notes mention some positive things. It sounds like a calm and good moment."
        if any(word in full_text for word in NEGATIVE_WORDS):
             return "You're feeling neutral despite some challenges mentioned. Staying balanced is a great strength."

    detected_contexts = detect_context(full_text)

    # 1. Check for specific keywords first (e.g. "tired")
    if "fatigue" in detected_contexts:
        if emotion in ["happy", "excited"]:
            return "It is great that you are happy, but you seem tired as well. Remember to get some rest."
        return "You seem tired. Remember that rest is productive too."
    
    if "academic pressure" in detected_contexts:
        if emotion in ["happy", "excited"]:
            return "It is impressive that you are staying positive despite the academic pressure!"
        return "School can be tough. Take it one assignment at a time."

    if "loneliness" in detected_contexts:
        return "Feeling alone is tough. Try to reach out to someone you trust today."
        
    if "emotional_release" in detected_contexts:
        return "Crying is a healthy way to release built-up emotion. It's okay to let it out."

    if "positive_events" in detected_contexts:
        if emotion in ["sad", "angry", "stressed", "anxious"]:
             return f"It seems like a significant event happened ({reason}). It's okay to have mixed feelings about it."
        
    if "technology" in detected_contexts:
        if emotion in ["happy", "excited"]:
            return "It's impressive that you're keeping your head up even when the system is crashing! Resilience is key."
        elif emotion in ["angry", "stressed", "sad", "anxious"]:
            return "Tech issues are the worst. Take a step back, maybe a 5-minute break will help clear the 'bug' in your mind too."

    if "achievement_success" in detected_contexts:
        if emotion in ["happy", "excited"]:
            return "You crushed it! Make sure to treat yourself for this win today."
        else:
            return "You achieved something great, but you still feel down. It's okay to feel 'post-project blues' after a big push."
        
    # 2.5 If no specific context but text is present, reflect it back
    if not detected_contexts and (reason or thought):
        # Smart Fallback: Use the emotion to frame the response even if we don't recognize the words
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

    # 2. Then check emotion categories

    if emotion in ["stressed", "anxious"]:
        if reason or thought:
            return (
                "It's okay to feel stressed. You've been dealing with a lot, "
                "and recognizing this is already a positive step."
            )
        else:
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
    
    # Analyze separately to distinguish Situation (External) vs Thoughts (Internal)
    reason_contexts = detect_context(reason) if reason else []
    thought_contexts = detect_context(thought) if thought else []
    
    # Combined for general checks
    detected_contexts = list(set(reason_contexts + thought_contexts))

    analysis = []
    suggestions = []
    
    # Get encouragement based on emotion
    encouragement = get_encouragement(emotion, detected_contexts)

    # --- Mixed Emotion Check ---
    is_mixed_feeling_pos = emotion in ["happy", "excited"] and any(word in full_text for word in NEGATIVE_WORDS)
    is_mixed_feeling_neg = emotion in ["sad", "angry", "stressed", "anxious"] and any(word in full_text for word in POSITIVE_WORDS)
    is_mixed_feeling_neutral_pos = emotion == "neutral" and any(word in full_text for word in POSITIVE_WORDS)
    is_mixed_feeling_neutral_neg = emotion == "neutral" and any(word in full_text for word in NEGATIVE_WORDS)

    # -------- ANALYSIS --------
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
            
            # situation-based on some keywords
            if "positive_events" in reason_contexts:
                analysis.append("Even positive life changes (eustress) can be physically and mentally draining.")
            elif "emotional_release" in reason_contexts:
                analysis.append("The urge to cry is a natural physiological response to release stress hormones.")
            elif "technology" in reason_contexts:
                analysis.append("Technical glitches or system crashes are frustrating because they disrupt your flow and sense of control.")            
            elif "academic pressure" in reason_contexts:
                analysis.append(f"Specifically, {reason} involves academic demands, which are a primary source of your current pressure.")           
            elif "work stress" in reason_contexts:
                analysis.append("Professional responsibilities or workplace dynamics seem to be weighing on your energy.")

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
            elif "loneliness" in reason_contexts:
                analysis.append("Isolation can amplify sadness; connection is often the antidote.")
                suggestions.append("Reach out to a friend or family member, even just for a quick chat")
            elif "positive_events" in reason_contexts:
                analysis.append("It is valid to feel sad even during happy events. This is often called 'paradoxical emotion'.")
            elif "technology" in reason_contexts:
                analysis.append("It’s valid to feel sad or defeated when tools you rely on fail you during important tasks.")
            elif not reason_contexts:
                analysis.append("Sometimes specific events trigger sadness because they touch on deeper values or needs.")

            if "emotional_release" in reason_contexts:
                analysis.append("Crying is often a necessary release valve for overwhelming feelings; it helps reset your nervous system.")

        if thought:
            if "self-esteem" in thought_contexts:
                analysis.append("Your internal monologue seems critical of yourself, which deepens the sadness.")
            elif "loneliness" in thought_contexts:
                analysis.append("You are telling yourself that you are alone, but this feeling is temporary.")
   
            if not any(ctx in thought_contexts for ctx in ["uncertainty", "self-esteem"]):
                analysis.append("Your thoughts suggest self-doubt or emotional disappointment.")
            
            if "emotional_release" in thought_contexts:
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
            if "technology" in reason_contexts:
                analysis.append("Staying positive despite technical hurdles is a sign of high resilience.")
            elif "achievement_success" in reason_contexts:
                analysis.append("You've clearly hit a milestone; acknowledging these wins builds long-term confidence.")
            elif "relationship issues" in reason_contexts:
                analysis.append("Resolving social friction or enjoying a good interaction is a great emotional boost.")
            elif "hobbies" in reason_contexts:
                analysis.append("Engaging in things you love is essential for your mental 'recharge'.")

            if not reason_contexts:
                analysis.append("Identifying these personal sources of happiness helps you build resilience.")

        if thought:
            if "self-esteem" in thought_contexts:
                analysis.append("Your thoughts reflect a healthy sense of self-worth right now.")
            elif "positive_events" in thought_contexts:
                analysis.append("You are actively focusing on the good, which helps strengthen your mental well-being.")
        
        suggestions.extend([
            "Take note of what contributed to this feeling",
            "Try to repeat or maintain these positive habits"
        ])

    elif emotion == "excited":
        analysis.append("Excitement indicates high energy and positive anticipation.")
        
        if reason:
            analysis.append(f"It is wonderful that '{reason}' has sparked this enthusiasm.")
            if "academic pressure" in reason_contexts or "work stress" in reason_contexts:
                analysis.append("You're turning a challenge into a motivation—this is a powerful 'flow state'.")
            elif "social_media" in reason_contexts:
                analysis.append("Positive digital interactions can be a great way to feel connected to your community.")
            elif "future_uncertainty" in reason_contexts:
                analysis.append("You're viewing the unknown as an opportunity rather than a threat. Keep that perspective!")
            
            if not reason_contexts:
                analysis.append("Passion for specific interests is a great fuel for mental well-being.")
        
        if thought:
            if "emotional_release" in thought_contexts:
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
            elif "technology" in reason_contexts:
                analysis.append("Handling tech issues with a neutral head is the most efficient way to problem-solve.")
            elif "academic pressure" in reason_contexts:
                analysis.append("Being objective about your workload helps you prioritize without getting paralyzed by stress.")
            
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
        
        if reason_contexts:
            analysis.append(f"It seems {', '.join(reason_contexts)} might be triggering this reaction.")
             
        elif not reason_contexts:
            analysis.append("Even if the trigger seems specific, anger often points to a need for change or boundaries.")

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

    # -------- GENERAL SUGGESTIONS (Fallback & Context-Specific) --------
    if "social_media" in detected_contexts:
        suggestions.append("Consider a short 'digital detox'")
        suggestions.append("Unfollow accounts that drain your energy")

    if "self-esteem" in detected_contexts:
        suggestions.append("Write down 3 things you value about yourself")
        suggestions.append("Remember: social media is a highlight reel, not reality")

    if "academic pressure" in detected_contexts or "work stress" in detected_contexts:
        suggestions.append("Try the Pomodoro technique: 25m focus, 5m break")
        suggestions.append("Celebrate small wins, even just finishing one task")

    if "financial" in detected_contexts:
        suggestions.append("Identify one small change to your budget")
        suggestions.append("Try a 'no-spend' day challenge")
    
    if "health concerns" in detected_contexts:
        suggestions.append("Listen to your body and rest if needed")
        suggestions.append("Stay hydrated and prioritize sleep")

    if "animal" in detected_contexts:
        suggestions.append("Spend some therapeutic time with your pet")

    if "fatigue" in detected_contexts:
        suggestions.append("Prioritize getting a good night's sleep")
        
    if "relationship issues" in detected_contexts:
        suggestions.append("Set healthy boundaries to protect your energy")
        suggestions.append("Communicate your needs clearly using 'I' statements")
    
    if "technology" in detected_contexts:
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

    if "achievement_success" in detected_contexts:
        suggestions.extend([
            "Treat yourself to your favorite drink or meal",
            "Take a screenshot of this success to look back on during hard days",
            "Take the rest of the day off if your schedule allows"
        ])

    # Ensure suggestions list is never empty
    if not suggestions:
        if emotion in ["stressed", "anxious", "angry"]:
            suggestions.append("Practice deep breathing exercises (4-7-8 technique)")
            suggestions.append("Take a 10-minute walk to clear your head")
            suggestions.append("Listen to a song that matches your current 'vibe' to process the feeling")
        elif emotion in ["sad", "neutral"]:
            suggestions.append("Do one small thing that usually brings you joy")
        elif emotion in ["happy", "excited"]:
            suggestions.append("Share your positive energy with someone else")

    # Remove duplicates while preserving order
    seen = set()
    suggestions = [x for x in suggestions if not (x in seen or seen.add(x))]

    # Limit to 5 suggestions max to avoid overwhelming the user
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
    # Sort logs by time
    logs.sort(key=lambda x: x['timestamp'])
    
    emotions = [l['emotion_name'] for l in logs]
    
    # --- NEW LOGIC: Mood Level Calculation (Aligns with Statistics Graph) ---
    mood_scores = {
        'Happy': 3, 'Excited': 3,
        'Neutral': 2,
        'Sad': 1, 'Anxious': 1, 'Stressed': 1, 'Angry': 1
    }
    
    scores = [mood_scores.get(e, 2) for e in emotions]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    main_emoji = "😐"
    main_icon = "neutral.png"
    
    # Thresholds: 1.0-1.66 (Neg), 1.67-2.33 (Neu), 2.34-3.0 (Pos)
    if avg_score >= 2.34:
        main_emotion = "Mostly Positive"
        main_emoji = "😊"
        main_icon = "happy.png"
    elif avg_score <= 1.66:
        main_emotion = "Mostly Negative"
        main_emoji = "😔"
        main_icon = "sad.png"
    else:
        # It is in the Neutral range (approx 2.0). Check if it's stable Neutral or Mixed.
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

    # Aggregate texts into a timeline format
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
    
    # Generate Analysis
    analysis = []
    suggestions = []
    
    # --- NEW RULE: Check for Specific Emotion Spikes (e.g. Angry > 3) ---
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

    # Add context specific advice
    if "academic pressure" in detected_contexts or "work stress" in detected_contexts:
        analysis.append(f"Work or school pressure was a recurring theme this {period_name}.")
        suggestions.append("Schedule downtime to prevent burnout.")

    if "relationship issues" in detected_contexts:
        analysis.append(f"Social interactions played a big role in your {period_name}.")
        suggestions.append("Set boundaries if interactions feel draining.")

    if "fatigue" in detected_contexts:
        analysis.append("You mentioned being tired multiple times; you might be running on empty.")
        suggestions.append("Prioritize sleep and rest above all else.")

    if "financial" in detected_contexts:
        suggestions.append("Focus on small, controllable financial steps.")

    if "health concerns" in detected_contexts:
        suggestions.append("Listen to your body and rest if needed.")

    if "social_media" in detected_contexts:
        suggestions.append("Consider a short digital detox.")

    # Fallback suggestions if empty
    if not suggestions:
        if main_emotion == "Mostly Negative":
             suggestions.append("Try a quick breathing exercise (4-7-8 technique).")
        elif main_emotion == "Mixed":
             suggestions.append("Journaling might help untangle mixed feelings.")
        elif main_emotion == "Mostly Positive":
             suggestions.append("Share your positive energy with others.")
        else:
             suggestions.append("Practice mindfulness to maintain balance.")

    # Remove duplicates while preserving order
    seen = set()
    suggestions = [x for x in suggestions if not (x in seen or seen.add(x))]

    # Limit to 5 suggestions max
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
    
    # Data containers
    single_data = None
    daily_data = None
    weekly_data = None
    monthly_data = None
    selected_date_str = None
    selected_month_str = None
    selected_week_str = None
    view_type = 'dashboard' # Default to dashboard view

    if log_id:
        # CASE 1: Specific Log Selected
        log = get_emolog_by_id(log_id)
        if log and log['username'] != username:
            flash("You do not have permission to view this log.", "error")
            return redirect(url_for('home.dashboard'))
        
        view_type = 'single'

    if not log_id:
        # CASE 2: No Log Selected -> Generate Summaries (Daily, Weekly, Monthly)
        all_logs = UserManager.get_emotion_logs(username)
        now = datetime.now()
        
        # --- 1. Daily Logs ---
        
        # Check for date parameter
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

        # --- 2. Weekly Logs ---
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
            # Default to Last 7 Days
            week_start = now - timedelta(days=7)
            week_end = now + timedelta(days=1)
            week_label = "Last 7 Days"
            # Set default ISO week for input
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

        # --- 3. Monthly Logs ---
        month_param = request.args.get('month')
        if month_param:
            selected_month_str = month_param
        else:
            selected_month_str = now.strftime('%Y-%m')
            
        monthly_logs = [l for l in all_logs if l['timestamp'].startswith(selected_month_str)]
        if monthly_logs:
            monthly_data = generate_aggregated_feedback(monthly_logs, "month")
            # Format nice month name
            dt_m = datetime.strptime(selected_month_str, '%Y-%m')
            monthly_data['timestamp'] = f"Monthly Summary - {dt_m.strftime('%B %Y')}"
        

    # If we have absolutely no data to show
    if not log and not daily_data and not weekly_data and not monthly_data: 
        return render_template("ai_feedback.html", empty=True)
    
    # Determine active tab based on request args
    active_tab = 'daily'
    if request.args.get('month'):
        active_tab = 'monthly'
    elif request.args.get('week'):
        active_tab = 'weekly'

    if log:
        # Standard Single Log Feedback
        log_data = dict(log)

        # 1. Try to load saved feedback from DB first
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