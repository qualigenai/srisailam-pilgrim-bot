import pytest
from app.agents.intent_classifier import classify_intent
from app.agents.greeting_agent import handle_greeting
from app.agents.booking_agent import handle_booking
from app.utils.error_handler import get_unknown_message, get_fallback_message

class TestIntentClassifier:

    def test_greeting_english(self):
        assert classify_intent("Hi") == "greeting"

    def test_greeting_namaste(self):
        assert classify_intent("Namaste") == "greeting"

    def test_greeting_jai_shiva(self):
        assert classify_intent("Jai Mallikarjuna") == "greeting"

    def test_greeting_telugu(self):
        assert classify_intent("నమస్కారం") == "greeting"

    def test_greeting_hindi(self):
        assert classify_intent("नमस्ते") == "greeting"

    def test_temple_info(self):
        assert classify_intent("What time does temple open?") == "temple_info"

    def test_booking_intent(self):
        assert classify_intent("How to book darshan tickets?") == "booking"

    def test_journey_intent(self):
        assert classify_intent("Coming from Hyderabad, 2 days, family of 4") == "journey"

    def test_ritual_intent(self):
        assert classify_intent("Which seva should I do for health?") == "ritual"

    def test_festival_intent(self):
        assert classify_intent("When is Maha Shivaratri?") == "festival"

    def test_closure_intent(self):
        assert classify_intent("Thank you") == "closure"

    def test_unknown_intent(self):
        assert classify_intent("What is the price of gold?") == "unknown"

    def test_telugu_journey(self):
        assert classify_intent("శ్రీశైలం వెళ్ళాలనుకుంటున్నాను 2 రోజులు") == "journey"

    def test_hindi_journey(self):
        assert classify_intent("श्रीशैलम जाना है 2 दिन") == "journey"


class TestGreetingAgent:

    def test_greeting_returns_string(self):
        result = handle_greeting()
        assert isinstance(result, str)

    def test_greeting_contains_mallikarjuna(self):
        result = handle_greeting()
        assert "Mallikarjuna" in result or "మల్లికార్జున" in result

    def test_greeting_contains_help_options(self):
        result = handle_greeting()
        assert len(result) > 50


class TestBookingAgent:

    def test_booking_returns_string(self):
        result = handle_booking()
        assert isinstance(result, str)

    def test_booking_contains_website(self):
        result = handle_booking()
        assert "srisailadevasthanam.org" in result

    def test_booking_contains_mana_mitra(self):
        result = handle_booking()
        assert "9552300009" in result

    def test_booking_contains_phone(self):
        result = handle_booking()
        assert "08524-288888" in result


class TestErrorHandler:

    def test_fallback_english(self):
        result = get_fallback_message("en")
        assert isinstance(result, str)
        assert len(result) > 10

    def test_fallback_telugu(self):
        result = get_fallback_message("te")
        assert isinstance(result, str)

    def test_fallback_hindi(self):
        result = get_fallback_message("hi")
        assert isinstance(result, str)

    def test_unknown_english(self):
        result = get_unknown_message("en")
        assert isinstance(result, str)
        assert "Srisailam" in result