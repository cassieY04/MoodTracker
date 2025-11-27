from typing import Optional

SECURITY_QUESTIONS = [
    "What is your favourite food?",
    "What was your dream car?",
    "What is your first phone brand?"
]

def password_requirement(password: str) -> Optional[str]:
    if len(password) < 8 or len(password) > 12:
        return "Password must be between 8 to 12 characters long."
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one digit."
    if not any(c in "@_-*#!%$&" for c in password):
        return "Password must contain at least one special character (@, _, -, *, #, !, %, $, or &)."
    return None  

def validate_email(email: str) -> bool:
    return isinstance(email,str) and email.endswith('@gmail.com')

def validate_phone(phone: str) -> bool:
    return phone.isdigit() and 8 <= len(phone) <= 12

def validate_security_question(question: str) -> bool:
    return question in SECURITY_QUESTIONS

def validate_security_answer(answer: str) -> bool:
    return bool(answer and answer.strip())