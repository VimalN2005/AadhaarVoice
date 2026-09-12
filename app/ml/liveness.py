"""
Liveness Challenge and Anti-Replay Engine.
Issues randomized single-use verbal challenges to prevent replay attacks and audio playback spoofs.
"""

import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

PHONETIC_DIGITS_EN = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
PHONETIC_DIGITS_HI = ["Shunya", "Ek", "Do", "Teen", "Chaar", "Paanch", "Chhah", "Saat", "Aath", "Nau"]

ACTION_WORDS = ["Verify", "Aadhaar", "Access", "Confirm", "Auth", "Secure", "Identity"]


def generate_challenge(demo_vid: str, expire_seconds: int = 120) -> Dict[str, Any]:
    """
    Generates a timed, randomized dynamic passphrase challenge.
    """
    challenge_id = str(uuid.uuid4())
    action = random.choice(ACTION_WORDS)
    digits = [random.randint(0, 9) for _ in range(4)]
    digits_str = "".join(str(d) for d in digits)

    phrase_text = f"{action} {digits_str}"
    en_phonetic = " ".join([action] + [PHONETIC_DIGITS_EN[d] for d in digits])
    hi_phonetic = " ".join([action] + [PHONETIC_DIGITS_HI[d] for d in digits])

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=expire_seconds)

    return {
        "challenge_id": challenge_id,
        "demo_vid": demo_vid,
        "passphrase_text": phrase_text,
        "passphrase_phonetic_en": en_phonetic,
        "passphrase_phonetic_hi": hi_phonetic,
        "expires_at": expires_at.isoformat(),
        "valid_duration_seconds": expire_seconds,
    }
