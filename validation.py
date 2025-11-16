def password_requirement(password):
    if len(password) < 8 or len(password) > 12:
        return "Password must be between 8 to 12 characters long."
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one digit."
    if not any(c in "@_-*#" for c in password):
        return "Password must contain at least one special character (@, _, - ,* or #)."
    return None  

def validate_email(email):
    return email.endswith('@gmail.com')

def validate_phone(phone):
    return phone.isdigit() and 8 <= len(phone) <= 12