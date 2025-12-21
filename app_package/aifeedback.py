from flask import Blueprint, render_template, session, redirect, url_for, flash
from .users import UserManager
import ast
from Databases.emologdb import get_latest_emolog, get_emolog_by_id


ai_feedback_bp = Blueprint('ai_feedback', __name__)
# Helper function to detect context from text
def detect_context(text):
    text = text.lower()
    context_map = {
        "academic pressure": ["exam", "study", "assignment", "deadline", "test", "school", "grade", "gpa", "class"],
        "fatigue": ["tired", "sleep", "exhausted", "burnt out", "insomnia", "nap", "drained", "fatigue"],
        "relationship issues": ["friend", "family", "partner", "argument", "fight", "conflict", "breakup", "toxic", "parents"],
        "health concerns": ["sick", "pain", "doctor", "ill", "headache", "hurt", "health", "body"],
        "work stress": ["job", "boss", "work", "salary", "meeting", "career", "colleague", "project"],
        "financial": ["money", "cost", "expensive", "debt", "pay", "broke", "bill", "rent"],
        "self-esteem": ["ugly", "fat", "stupid", "hate myself", "useless", "failure", "worthless", "confidence"],
        "loneliness": ["lonely", "alone", "isolated", "nobody", "ignored", "miss"],
        "uncertainty": ["future", "confused", "lost", "unsure", "what if", "decision"],
        "hobbies": ["game", "music", "read", "sport", "art", "draw", "code", "movie"]
    }
    detected = []
    for category, keywords in context_map.items():
        if any(word in text for word in keywords):
            detected.append(category)
    return detected

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
        
    # 2.5 If no specific context but text is present, reflect it back
    if not detected_contexts and (reason or thought):
        return f"It sounds like {reason if reason else 'your situation'} is impacting you. Feeling {emotion} is valid."

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
    full_text = f"{reason} {thought}"
    detected_contexts = detect_context(full_text)

    analysis = []
    suggestions = []
    
    # Helper to join contexts naturally
    context_str = ", ".join(detected_contexts)

    # -------- ANALYSIS --------
    if emotion in ["stressed", "anxious"]:
        analysis.append("Your emotional state suggests you may be experiencing pressure or overload.")

        if reason:
            analysis.append(f"You identified '{reason}' as a key factor.")
            if detected_contexts:
                analysis.append(f"Specifically, {context_str} seems to be a significant source of this pressure.")
            

        if thought:
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
             if "relationship issues" in detected_contexts:
                 analysis.append("Interpersonal conflicts can be draining; try to protect your peace.")
             elif "self-esteem" in detected_contexts:
                 analysis.append("Be gentle with yourself; you are more than your current struggles.")
             elif "loneliness" in detected_contexts:
                 analysis.append("Isolation can amplify sadness; connection is often the antidote.")
                 suggestions.append("Reach out to a friend or family member, even just for a quick chat")

        if thought:
            analysis.append("Your thoughts suggest self-doubt or emotional disappointment.")

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

        suggestions.extend([
            "Take note of what contributed to this feeling",
            "Try to repeat or maintain these positive habits"
        ])

    elif emotion == "excited":
        analysis.append("Excitement indicates high energy and positive anticipation.")
        
        if reason:
            analysis.append(f"It is wonderful that '{reason}' has sparked this enthusiasm.")
        
        suggestions.extend([
            "Channel this energy into a creative project",
            "Share your good news with a friend",
            "Write down this moment to remember it later"
        ])

    elif emotion == "neutral":
        analysis.append("A neutral mood signifies stability and a lack of overwhelming emotion.")
        
        if reason:
             analysis.append(f"Your note about '{reason}' suggests a grounded perspective.")
             
        suggestions.extend([
            "Use this clarity to plan your week",
            "Practice mindfulness to maintain this balance",
            "Engage in a low-stress hobby like reading"
        ])

    elif emotion == "angry":
        analysis.append("Anger often signals that a boundary has been crossed or a need unmet.")
        
        if reason:
            analysis.append(f"It is understandable that '{reason}' would cause frustration.")
        
        if detected_contexts:
             analysis.append(f"It seems {context_str} might be triggering this reaction.")
             
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
        "summary": f"You are feeling {emotion.lower()}.",
        "causes": analysis,
        "suggestions": suggestions,
        "reflection": {
            "reason": reason,
            "thought": thought
        }
    }
    
@ai_feedback_bp.route("/ai_feedback")
@ai_feedback_bp.route("/ai_feedback/<int:log_id>")
def ai_feedback(log_id=None):
    username = session.get("username")
    if not username:
        return redirect("/login")
    
    if log_id:
        log = get_emolog_by_id(log_id)
        # Security: Ensure the log belongs to the current user
        if log and log['username'] != username:
            flash("You do not have permission to view this log.", "error")
            return redirect(url_for('home.dashboard'))
    else:
        log = get_latest_emolog(username)

    if not log: 
        return render_template("ai_feedback.html", empty=True)
    
    # Convert sqlite3.Row to dict to allow .get()
    log_data = dict(log)

    # 1. Try to load saved feedback from DB first (Preserve History)
    full = None
    if log_data.get("ai_full_feedback"):
        try:
            full = ast.literal_eval(log_data["ai_full_feedback"])
        except (ValueError, SyntaxError):
            full = None

    # 2. If missing or invalid, regenerate it
    if not full:
        full = generate_full_feedback(
            log_data["emotion_name"],
            log_data["note"] or "",
            log_data.get("thought", "")
        )
    
    from .logemotion import get_emotion_styling
    style = get_emotion_styling(log_data["emotion_name"])

    return render_template(
        "ai_feedback.html",
        emotion=full["emotion"],
        emoji=style["emoji"],
        summary=full["summary"],
        causes=full["causes"],
        suggestions=full["suggestions"],
        reason=full["reflection"]["reason"],
        thought=full["reflection"]["thought"],
        log_id=log_id
    )