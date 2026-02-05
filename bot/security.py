"""Security: prompt injection detection"""

import re
import json
import logging
from pathlib import Path

logger = logging.getLogger("bot.security")


def load_injection_patterns() -> list[dict]:
    """Load prompt injection patterns from JSON file"""
    patterns_file = Path(__file__).parent / "prompt-injection-patterns.json"
    if patterns_file.exists():
        try:
            with open(patterns_file) as f:
                data = json.load(f)
                patterns = data.get("patterns", [])
                logger.info(f"Loaded {len(patterns)} prompt injection patterns")
                return patterns
        except Exception as e:
            logger.error(f"Failed to load patterns: {e}")
    logger.warning("No prompt-injection-patterns.json found, using defaults")
    return []


INJECTION_PATTERNS = load_injection_patterns()


def detect_prompt_injection(text: str) -> bool:
    """Check if text contains prompt injection patterns"""
    for pattern_info in INJECTION_PATTERNS:
        pattern = pattern_info.get("pattern", "")
        try:
            if re.search(pattern, text, re.IGNORECASE):
                reason = pattern_info.get("reason", "Unknown")
                logger.warning(f"[INJECTION] Detected: {reason}")
                return True
        except re.error:
            continue
    return False
