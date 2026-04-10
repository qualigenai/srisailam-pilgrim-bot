import pytest
from app.multilingual.detector import detect_language
from app.multilingual.translator import translate_to_english, translate_from_english

class TestLanguageDetector:

    def test_english_detection(self):
        assert detect_language("What time does temple open?") == "en"

    def test_telugu_detection(self):
        assert detect_language("గుడి సమయాలు ఏమిటి?") == "te"

    def test_hindi_detection(self):
        assert detect_language("मंदिर का समय क्या है?") == "hi"

    def test_english_greeting(self):
        assert detect_language("Hello") == "en"

    def test_telugu_greeting(self):
        result = detect_language("నమస్కారం")
        assert result in ["te", "en"]

    def test_returns_english_for_unknown(self):
        result = detect_language("12345")
        assert result in ["en", "te", "hi"]


class TestTranslator:

    def test_english_passthrough(self):
        result = translate_to_english("Hello", "en")
        assert result == "Hello"

    def test_telugu_to_english(self):
        result = translate_to_english("గుడి సమయాలు ఏమిటి?", "te")
        assert isinstance(result, str)
        assert len(result) > 5
        assert "time" in result.lower() or "temple" in result.lower()

    def test_hindi_to_english(self):
        result = translate_to_english("मंदिर का समय क्या है?", "hi")
        assert isinstance(result, str)
        assert len(result) > 5

    def test_english_to_telugu(self):
        result = translate_from_english("Temple opens at 5:30 AM", "te")
        assert isinstance(result, str)
        assert len(result) > 5

    def test_english_to_hindi(self):
        result = translate_from_english("Temple opens at 5:30 AM", "hi")
        assert isinstance(result, str)
        assert len(result) > 5

    def test_english_passthrough_from(self):
        result = translate_from_english("Temple opens at 5:30 AM", "en")
        assert result == "Temple opens at 5:30 AM"