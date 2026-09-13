import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(email) and bool(EMAIL_REGEX.match(email.strip()))


def is_valid_phone(phone: str) -> bool:
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    return 7 <= len(digits) <= 15


def is_valid_pincode(pincode: str) -> bool:
    return bool(pincode) and bool(re.match(r"^\d{4,10}$", pincode.strip()))


def require_fields(data: dict, fields: list):
    """Returns a list of missing/empty field names."""
    missing = []
    for f in fields:
        value = data.get(f)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(f)
    return missing
