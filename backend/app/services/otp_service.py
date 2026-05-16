import random
import string
import sys
from datetime import datetime, timedelta, timezone

def generate_otp_code(length: int = 6) -> str:
    """Génère un code numérique aléatoire."""
    return "".join(random.choices(string.digits, k=length))

def send_otp_simulated(phone_number: str, code: str):
    """
    Simule l'envoi d'un OTP.
    En production, cela enverrait un email ou un SMS.
    """
    print("\n" + "!" * 60)
    print(f"!!! CODE OTP ENVOYÉ AU {phone_number} : {code} !!!")
    print("!" * 60 + "\n")
    sys.stdout.flush()
