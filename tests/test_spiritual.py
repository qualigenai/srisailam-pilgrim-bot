import pytest
from app.agents.spiritual_agent import (
    process_spiritual_message,
    is_seva_recommendation_request,
    is_mantra_request,
    is_preparation_request,
    is_prasadam_request,
    detect_intention,
    FOLLOW_UP_QUESTION
)

class TestSpiritualDetection:

    def test_seva_recommendation_detected(self):
        assert is_seva_recommendation_request("Which seva should I do?") == True

    def test_mantra_detected(self):
        assert is_mantra_request("Tell me about Om Namah Shivaya") == True

    def test_preparation_detected(self):
        assert is_preparation_request("How to prepare for Sparsha Darshan?") == True

    def test_prasadam_detected(self):
        assert is_prasadam_request("What prasadam is available?") == True

    def test_general_not_seva(self):
        assert is_seva_recommendation_request("What time does temple open?") == False


class TestIntentionDetection:

    def test_health_intention(self):
        result = detect_intention("I want to pray for my mother's health")
        assert result == "health"

    def test_prosperity_intention(self):
        result = detect_intention("I want blessings for wealth and prosperity")
        assert result == "prosperity"

    def test_family_intention(self):
        result = detect_intention("Praying for family harmony and marriage")
        assert result == "family"

    def test_general_intention(self):
        result = detect_intention("Which seva should I do?")
        assert result in ["general", "health", "prosperity", "family",
                         "education", "moksha", "obstacles"]


class TestSpiritualMessages:

    def test_follow_up_question_english(self):
        assert isinstance(FOLLOW_UP_QUESTION["en"], str)
        assert "1️⃣" in FOLLOW_UP_QUESTION["en"]

    def test_follow_up_question_telugu(self):
        assert isinstance(FOLLOW_UP_QUESTION["te"], str)

    def test_follow_up_question_hindi(self):
        assert isinstance(FOLLOW_UP_QUESTION["hi"], str)

    def test_process_vague_seva(self):
        result = process_spiritual_message(
            "Which seva should I do?", "test_phone", "en"
        )
        assert isinstance(result, str)
        assert len(result) > 20

    def test_process_health_seva(self):
        result = process_spiritual_message(
            "Which seva for my mother's health?", "test_phone", "en"
        )
        assert isinstance(result, str)
        assert len(result) > 20

    def test_process_mantra(self):
        result = process_spiritual_message(
            "Tell me about Om Namah Shivaya", "test_phone", "en"
        )
        assert isinstance(result, str)
        assert len(result) > 20

    def test_process_under_1500_chars(self):
        result = process_spiritual_message(
            "Which seva for health?", "test_phone", "en"
        )
        assert len(result) <= 1500