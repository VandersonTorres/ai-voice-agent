DEFAULT_VOICE = "en-US-JennyNeural"

VOICE_BY_LANGUAGE = {
    # Portuguese
    "pt": "pt-BR-FranciscaNeural",
    # English
    "en": "en-US-JennyNeural",
    # Spanish
    "es": "es-ES-ElviraNeural",
    # French
    "fr": "fr-FR-DeniseNeural",
    # Deutsch
    "de": "de-DE-KatjaNeural",
    # Italian
    "it": "it-IT-ElsaNeural",
    # Mandarin (Simplified Chinese)
    "zh": "zh-CN-XiaoxiaoNeural",
    # Japanese
    "ja": "ja-JP-NanamiNeural",
    # Korean
    "ko": "ko-KR-SunHiNeural",
    # Russian
    "ru": "ru-RU-SvetlanaNeural",
    # Arabic
    "ar": "ar-SA-ZariyahNeural",
    # Hindi
    "hi": "hi-IN-SwaraNeural",
}

RATE_BY_LANGUAGE = {
    "pt": "+2%",
    "en": "+2%",
    "de": "+0%",
    "zh": "-5%",  # Chinese voices tend to sound better with a slower rate
    "ja": "-3%",
}
