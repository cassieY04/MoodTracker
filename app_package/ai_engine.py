# ai_engine.py
# Level 2.5 Rule-Based AI Emotion Analysis Engine

def normalize_text(*texts):
    """
    Combine emotion, reason, thought into one lowercase string
    """
    return " ".join(t for t in texts if t).lower()


# --------------------------------------------------
# SHORT FEEDBACK (for Log Emotion popup)
# --------------------------------------------------
def generate_short_feedback(emotion, reason="", thought=""):
    text = normalize_text(emotion, reason, thought)

    base = f"It's okay to feel {emotion.lower()}. "

    if emotion == "Stressed":
        if any(w in text for w in ["assignment", "deadline", "busy", "pressure", "tired", "overwhelmed"]):
            return base + "You've been dealing with a lot. Try slowing down and focusing on one task at a time."
        return base + "Recognizing stress is already a positive step."

    if emotion == "Sad":
        if any(w in text for w in ["alone", "miss", "fail", "lost", "disappointed"]):
            return base + "You may be feeling emotionally drained. Be gentle with yourself."
        return base + "It's okay to sit with this feeling for a while."

    if emotion == "Anxious":
        if any(w in text for w in ["future", "exam", "uncertain", "worry", "scared"]):
            return base + "Uncertainty can increase anxiety. Try grounding yourself in the present."
        return base + "Taking a few deep breaths may help."

    if emotion == "Angry":
        if any(w in text for w in ["unfair", "ignored", "frustrated", "annoyed"]):
            return base + "Anger often comes from unmet needs or boundaries."
        return base + "Pausing before reacting can help."

    if emotion == "Happy":
        return base + "Enjoy this positive moment and acknowledge what's going well."

    if emotion == "Excited":
        return base + "Your enthusiasm shows positive energy. Keep it going."

    if emotion == "Neutral":
        return base + "A calm state can be a good opportunity to reflect."

    return base + "Noticing your emotions is meaningful."


# --------------------------------------------------
# ANALYSIS ENGINE (used by full feedback)
# --------------------------------------------------
def analyze_input(emotion, reason="", thought=""):
    text = normalize_text(emotion, reason, thought)

    causes = []
    suggestions = []

    if any(w in text for w in ["assignment", "exam", "deadline", "study"]):
        causes.append("academic pressure")
        suggestions.append("break tasks into smaller steps")

    if any(w in text for w in ["sleep", "tired", "rest", "exhausted"]):
        causes.append("lack of rest")
        suggestions.append("prioritize sleep and recovery")

    if any(w in text for w in ["alone", "ignored", "nobody"]):
        causes.append("social isolation")
        suggestions.append("reach out to someone you trust")

    if any(w in text for w in ["fail", "not good enough", "behind"]):
        causes.append("self-expectation")
        suggestions.append("practice self-compassion")

    if not causes:
        causes.append("general emotional fluctuation")
        suggestions.append("continue observing your emotions")

    return {
        "emotion": emotion,
        "causes": list(set(causes)),
        "suggestions": list(set(suggestions))
    }


# --------------------------------------------------
# FULL FEEDBACK (for AI Feedback page)
# --------------------------------------------------
def generate_full_feedback(emotion, reason="", thought=""):
    analysis = analyze_input(emotion, reason, thought)

    return {
        "emotion": analysis["emotion"],
        "summary": f"You logged feeling {analysis['emotion']} recently.",
        "causes": analysis["causes"],
        "suggestions": analysis["suggestions"],
        "reflection": {
            "reason": reason if reason else "No reason provided.",
            "thought": thought if thought else "No specific thought recorded."
        }
    }
