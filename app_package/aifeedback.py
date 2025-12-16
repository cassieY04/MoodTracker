from flask import Blueprint, render_template, session, redirect, url_for, flash

ai_feedback_bp = Blueprint('ai_feedback', __name__)

def generate_ai_feedback(emotion, reason):
    emotion_lower = (emotion or "").lower()
    reason = (reason or "").lower()
    
    #look emotion 
    if emotion_lower == "happy":
        base = "It's great to see you're feeling happy! "
    elif emotion_lower == "sad":
        base = "I'm sorry to hear you're feeling sad. "
    elif emotion_lower == "angry":
        base = "It's understandable to feel angry sometimes. "
    elif emotion_lower == "anxious":
        base = "Feeling anxious can be tough. "
    elif emotion_lower == "excited":
        base = "It's wonderful that you're feeling excited! "
    elif emotion_lower == "neutral":
        base = "Thanks for sharing your neutral feelings. "
    elif emotion_lower == "stressed":
        base = "It's okay to feel stressed. "
    else:
        base = "Thank you for sharing your feelings. "
        
    #look reason
    if any(word in reason for word in ["work", "job", "career"]):
        detail = "Work-related matters can significantly impact our emotions. "
    elif any(word in reason for word in ["family", "friends", "relationship"]):
        detail = "Relationships can strongly affect our emotions. Talking things out through can help. "
    elif any(word in reason for word in ["health", "sick", "doctor"]):
        detail = "Health issues can be a major source of emotional stress. Taking care of yourself is important. "
    elif any(word in reason for word in ["school", "exam", "study"]):
        detail = "Academic pressures can be challenging. Remember to take breaks and manage your time well. "
    elif any(word in reason for word in ["money", "finance", "bills"]):
        detail = "Financial concerns can lead to stress. Creating a budget might help alleviate some worries. "
    elif any(word in reason for word in ["weather", "season", "sunny", "rainy"]):
        detail = "Weather changes can influence our mood. Getting some fresh air or sunlight might help. "
    elif any(word in reason for word in ["hobby", "fun", "leisure"]):
        detail = "Engaging in hobbies and leisure activities can boost your mood. Keep enjoying what you love! "
    elif any(word in reason for word in ["sleep", "tired", "rest"]):
        detail = "Lack of sleep can affect your emotions. Ensuring you get enough rest is crucial. "
    elif any(word in reason for word in ["social media", "internet", "phone"]):
        detail = "Spending too much time on social media can impact your mood. Consider taking breaks from screens. "
    else:
        detail = "Reflecting on the reasons behind your emotions can provide valuable insights. "
        
    return base + detail
    
@ai_feedback_bp.route("/ai_feedback")
def ai_feedback():
    emotion = session.get("emotion")
    reason = session.get("reason")
    feedback = generate_ai_feedback(emotion, reason)
    session.pop("emotion", None)
    session.pop("reason", None)
    return render_template("ai_feedback.html", feedback=feedback , emotion=emotion, reason=reason)
