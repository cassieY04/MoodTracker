from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash

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

def hash_password(password: str) -> str:
    """Return a hashed version of the password."""
    return generate_password_hash(password)

def verify_password(hashed_password: str, plain_password: str) -> bool:
    """Check if a plaintext password matches the hashed password."""
    return check_password_hash(hashed_password, plain_password) 

def validate_email(email: str) -> bool:
    return isinstance(email,str) and email.endswith('@gmail.com')

def validate_phone(phone: str) -> bool:
    return phone.isdigit() and 8 <= len(phone) <= 12

def validate_security_question(question: str,allowed_questions) -> str | None:
    if not question:
        return "Please select a security question."
    if question not in allowed_questions:
        return "Invalid security question selection."
    return None

def validate_security_answer(answer: str)-> str | None:
    if not answer or not answer.strip():
        return "Please provide an answer for the security question."
    return None