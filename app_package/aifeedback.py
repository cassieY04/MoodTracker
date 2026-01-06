from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from .users import UserManager
import ast
import random
from datetime import datetime, timedelta
from collections import Counter
from Databases.emologdb import get_latest_emolog, get_emolog_by_id


ai_feedback_bp = Blueprint('ai_feedback', __name__)
# Helper function to detect context from text
def detect_context(text):
    text = text.lower()
    context_map = {
        "academic pressure": [
            "exam", "study", "assignment", "deadline", "test", "school", "grade", "gpa", "class",
            "quiz", "midterm", "final", "thesis", "fyp", "project", "presentation", "lecture", "tutorial",
            "lab", "semester", "submission", "due", "fail", "pass", "resit", "repeat", "transcript",
            "scholarship", "tuition", "fees", "enrollment", "coursework", "syllabus", "lecturer", "professor",
            "tutor", "dean", "campus", "university", "college", "uni", "degree", "diploma", "group project",
            "capstone", "internship", "practicum", "viva", "research", "paper", "essay"
        ],
        "fatigue": [
            "tired", "sleep", "exhausted", "burnt out", "insomnia", "nap", "drained", "fatigue",
            "all-nighter", "sleepy", "zombie", "caffeine", "coffee", "energy drink", "no sleep", "awake",
            "burnout", "overworked", "collapse", "rest", "bed", "pillow", "woke up"
        ],
        "relationship issues": [
            "friend", "family", "partner", "argument", "fight", "conflict", "breakup", "toxic", "parents",
            "crush", "ghosted", "situationship", "roommate", "housemate", "drama", "gossip", "red flag", "bestie",
            "squad", "peer", "social", "reject", "dumped", "cheated", "ex", "boyfriend", "girlfriend", "bf", "gf",
            "tea", "ick", "trust", "lie", "betray", "jealous", "envy", "date", "dating", "marriage", "divorce"
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
            "office", "business"
        ],
        "financial": [
            "money", "cost", "expensive", "debt", "pay", "broke", "bill", "rent",
            "loan", "allowance", "budget", "save", "spend", "price", "cash", "wallet",
            "bank", "transfer", "shopping", "buy", "purchase", "afford", "cheap"
        ],
        "self-esteem": [
            "ugly", "fat", "stupid", "hate myself", "useless", "failure", "worthless", "confidence",
            "cringe", "awkward", "insecure", "imposter", "disappointment", "compare", "loser", "dumb", "flop",
            "mistake", "guilt", "shame", "embarrassed", "regret", "fault"
        ],
        "loneliness": [
            "lonely", "alone", "isolated", "nobody", "ignored", "miss",
            "left out", "excluded", "no friends", "homesick", "empty", "silence"
        ],
        "uncertainty": [
            "future", "confused", "lost", "unsure", "what if", "decision",
            "career path", "choice", "doubt", "worry", "scared", "change", "risk", "maybe", "plan"
        ],
        "hobbies": [
            "game", "music", "read", "sport", "art", "draw", "code", "movie",
            "gaming", "valorant", "league", "netflix", "binge", "gym", "workout", "spotify", "concert",
            "travel", "food", "eat", "football", "basketball", "badminton", "hiking", "swim", "dance",
            "anime", "manga", "series", "cook", "bake", "write", "sing", "guitar", "piano"
        ],
        "positive_events": [
            "party", "holiday", "vacation", "trip", "promotion", "date", "celebrate", "winning", "won", "success", "bonus", "award",
            "ace", "aced", "graduate", "convo", "internship", "offer", "hired", "vibe", "chill", "relax", "fun", "happy",
            "slay", "ate", "gift", "present", "surprise", "lucky", "blessed"
        ],
        "emotional_release": [
            "cry", "crying", "tears", "sob", "weep", "bawling", "break down", "teary",
            "scream", "yell", "vent", "rant", "explode", "meltdown"
        ],
        "social_media": [
            "instagram", "tiktok", "twitter", "x", "facebook", "snapchat", "story", "post", "like", "comment",
            "follower", "viral", "trend", "feed", "scroll", "screen", "phone", "notification", "dm", "message",
            "reply", "block", "unfollow"
        ],
        "technology": [
            "wifi", "internet", "lag", "slow", "crash", "bug", "error", "laptop", "pc", "computer", "battery",
            "charge", "broken", "screen", "mouse", "keyboard"
        ],
        "transport": [
            "bus", "train", "mrt", "lrt", "grab", "taxi", "car", "drive", "traffic", "jam", "late", "wait",
            "parking", "road", "accident"
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
            "Happiness looks good on you! Keep this momentum going."
        ],
        "excited": [
            "Ride this wave of energy! You are capable of amazing things.",
            "Your enthusiasm is your superpower today.",
            "Go for it! The world is ready for your energy."
        ],
        "neutral": [
            "Peace is power. Enjoy the calm in the chaos.",
            "A quiet mind is a creative mind. Use this balance wisely.",
            "It's okay to just 'be'. Not every day needs to be a rollercoaster."
        ],
        "sad": [
            "This feeling is temporary, but your strength is permanent.",
            "It's okay not to be okay. Be gentle with yourself today.",
            "Stars can't shine without darkness. You will get through this."
        ],
        "anxious": [
            "You are stronger than your anxiety. One breath at a time.",
            "Don't believe everything you think. You are safe right now.",
            "Focus on what you can control, and let go of what you can't."
        ],
        "stressed": [
            "You have survived 100% of your bad days. You've got this.",
            "Rest is not a reward; it's a necessity. Take a break.",
            "One step at a time. You don't have to solve everything today."
        ],
        "angry": [
            "Your feelings are valid, but don't let them consume you.",
            "Take a deep breath. You are in control, not your anger.",
            "Channel this energy into something that serves you, not hurts you."
        ]
    }
    
    # Default fallback
    options = messages.get(emotion, ["Trust the process. You are doing your best."])
    return random.choice(options)

def generate_short_feedback(emotion, reason="", thought=""):
    emotion = emotion.lower()
    # Combine text for analysis
    full_text = f"{reason} {thought}"
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
    
    # Analyze separately to distinguish Situation (External) vs Thoughts (Internal)
    reason_contexts = detect_context(reason) if reason else []
    thought_contexts = detect_context(thought) if thought else []
    
    # Combined for general checks
    detected_contexts = list(set(reason_contexts + thought_contexts))

    analysis = []
    suggestions = []
    
    # Get encouragement based on emotion
    encouragement = get_encouragement(emotion, detected_contexts)

    # -------- ANALYSIS --------
    if emotion in ["stressed", "anxious"]:
        analysis.append("Your emotional state suggests you may be experiencing pressure or overload.")

        if reason:
            analysis.append(f"You identified '{reason}' as a key factor.")
            if reason_contexts:
                analysis.append(f"Specifically, the situation involves {', '.join(reason_contexts)}, which is a common source of pressure.")
            
            else:
                analysis.append("External stressors like this often contribute to a sense of being overwhelmed, regardless of the specific cause.")

            if "positive_events" in reason_contexts:
                analysis.append("Even positive life changes (eustress) can be physically and mentally draining.")
            
            if "emotional_release" in reason_contexts:
                analysis.append("The urge to cry is a natural physiological response to release stress hormones.")
            

        if thought:
            if "uncertainty" in thought_contexts:
                analysis.append("Your thoughts are focused on the unknown, which fuels anxiety.")
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
             elif not reason_contexts:
                 analysis.append("Sometimes specific events trigger sadness because they touch on deeper values or needs.")
             elif "emotional_release" in reason_contexts:
                 analysis.append("Crying is often a necessary release valve for overwhelming feelings; it helps reset your nervous system.")

        if thought:
            if "self-esteem" in thought_contexts:
                analysis.append("Your internal monologue seems critical of yourself, which deepens the sadness.")
            elif "loneliness" in thought_contexts:
                analysis.append("You are telling yourself that you are alone, but this feeling is temporary.")
            else:
                analysis.append("Your thoughts suggest self-doubt or emotional disappointment.")
            
            if "emotional_release" in thought_contexts:
                analysis.append("Thinking about crying indicates you are reaching a point of emotional overflow.")

        if "fatigue" in detected_contexts:
            suggestions.append("Prioritize getting a good night's sleep tonight.")

        suggestions.extend([
            "Allow yourself time to process these feelings",
            "Consider talking to someone you trust",
            "Engage in a calming or comforting activity"
        ])

    elif emotion == "happy":
        analysis.append("Your positive mood suggests emotional balance and satisfaction.")
        
        if reason:
            analysis.append(f"It is great that '{reason}' is bringing you joy.")
            if not reason_contexts:
                analysis.append("Identifying these personal sources of happiness helps you build resilience.")

        suggestions.extend([
            "Take note of what contributed to this feeling",
            "Try to repeat or maintain these positive habits"
        ])

    elif emotion == "excited":
        analysis.append("Excitement indicates high energy and positive anticipation.")
        
        if reason:
            analysis.append(f"It is wonderful that '{reason}' has sparked this enthusiasm.")
            if not reason_contexts:
                analysis.append("Passion for specific interests is a great fuel for mental well-being.")
        
        suggestions.extend([
            "Channel this energy into a creative project",
            "Share your good news with a friend",
            "Write down this moment to remember it later"
        ])

    elif emotion == "neutral":
        analysis.append("A neutral mood signifies stability and a lack of overwhelming emotion.")
        
        if reason:
             analysis.append(f"Your note about '{reason}' suggests a grounded perspective.")
             if not reason_contexts:
                 analysis.append("Taking a step back to view things neutrally is a valuable skill.")
             
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

        if "emotional_release" in detected_contexts:
             analysis.append("Sometimes anger can manifest as tears (angry crying) when we feel powerless or overwhelmed.")

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
    if "financial" in detected_contexts:
        suggestions.append("Review your budget and identify one small change you can make")
    
    if "health concerns" in detected_contexts:
        suggestions.append("Listen to your body and rest if needed")
    
    # Ensure suggestions list is never empty
    if not suggestions:
        if emotion in ["stressed", "anxious", "angry"]:
             suggestions.append("Practice deep breathing exercises (4-7-8 technique)")
             suggestions.append("Take a 10-minute walk to clear your head")
        elif emotion in ["sad", "neutral"]:
             suggestions.append("Do one small thing that usually brings you joy")
        elif emotion in ["happy", "excited"]:
             suggestions.append("Share your positive energy with someone else")

    # Remove duplicates while preserving order
    seen = set()
    suggestions = [x for x in suggestions if not (x in seen or seen.add(x))]

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
    unique_emotions = set(emotions)
    
    # Check for mixed emotions
    positives = {"Happy", "Excited"}
    negatives = {"Sad", "Angry", "Anxious", "Stressed"}
    has_pos = bool(unique_emotions & positives)
    has_neg = bool(unique_emotions & negatives)
    
    main_emoji = "📅"
    if has_pos and has_neg:
        main_emotion = "Mixed Emotions"
        main_emoji = "🔀"
    else:
        # Find most frequent emotion
        most_common = Counter(emotions).most_common(1)[0][0]
        main_emotion = f"Mostly {most_common}"
        # We will let the template handle the emoji or pass a generic one

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
    
    if main_emotion == "Mixed Emotions":
        analysis.append(f"Your {period_name} was an emotional rollercoaster, shifting between highs and lows.")
        analysis.append("Fluctuations like this are normal during busy or eventful periods.")
        suggestions.append("Take a moment to decompress and process these events.")
    elif has_neg:
        analysis.append(f"It seems this {period_name} has been generally challenging for you.")
        suggestions.append("Be gentle with yourself; rest is important.")
    elif has_pos:
        analysis.append(f"You've had a generally positive {period_name}!")
        suggestions.append("Reflect on what went well so you can maintain this momentum.")
    else:
        analysis.append(f"Your {period_name} has been relatively stable.")

    # Add context specific advice
    if "academic pressure" in detected_contexts:
        analysis.append("School work was a recurring theme throughout your day.")
    if "relationship issues" in detected_contexts:
        analysis.append("Social interactions played a big role in your day.")
    if "fatigue" in detected_contexts:
        analysis.append("You mentioned being tired multiple times; you might be running on empty.")
        suggestions.append("Prioritize sleep tonight above all else.")

    return {
        "emotion": main_emotion,
        "emoji": main_emoji,
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