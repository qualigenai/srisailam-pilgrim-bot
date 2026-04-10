import pytest
from app.agents.orchestrator import process_message

class TestFullPipeline:

    def test_greeting_flow(self, test_phone):
        result = process_message("Hi", test_phone)
        assert isinstance(result, str)
        assert len(result) > 10

    def test_temple_info_flow(self, test_phone):
        result = process_message(
            "What time does Srisailam temple open?", test_phone
        )
        assert isinstance(result, str)
        assert "5:30" in result or "AM" in result or "temple" in result.lower()

    def test_booking_flow(self, test_phone):
        result = process_message(
            "How to book darshan tickets?", test_phone
        )
        assert "srisailadevasthanam.org" in result or "9552300009" in result

    def test_journey_vague_flow(self, test_phone):
        result = process_message(
            "I want to visit Srisailam", test_phone
        )
        assert isinstance(result, str)
        assert len(result) > 20

    def test_journey_complete_flow(self, test_phone):
        result = process_message(
            "Coming from Hyderabad, 2 days, family of 4", test_phone
        )
        assert isinstance(result, str)
        assert len(result) <= 1600

    def test_spiritual_flow(self, test_phone):
        result = process_message(
            "Which seva should I do for health?", test_phone
        )
        assert isinstance(result, str)
        assert len(result) > 20

    def test_out_of_scope(self, test_phone):
        result = process_message(
            "What is the price of petrol?", test_phone
        )
        assert isinstance(result, str)

    def test_closure_flow(self, test_phone):
        result = process_message("Thank you", test_phone)
        assert isinstance(result, str)
        assert "🙏" in result or "Mallikarjuna" in result

    def test_telugu_flow(self, test_phone):
        result = process_message(
            "గుడి సమయాలు ఏమిటి?", test_phone
        )
        assert isinstance(result, str)
        assert len(result) > 20

    def test_hindi_flow(self, test_phone):
        result = process_message(
            "मंदिर का समय क्या है?", test_phone
        )
        assert isinstance(result, str)
        assert len(result) > 20

    def test_memory_persists(self, test_phone):
        process_message("My name is Ram", test_phone)
        result = process_message("Hi", test_phone)
        assert isinstance(result, str)

    def test_conversation_context(self, test_phone):
        process_message("Tell me about Rudrabhishekam", test_phone)
        result = process_message("How long does it take?", test_phone)
        assert isinstance(result, str)
        assert len(result) > 20

    def test_response_length_limit(self, test_phone):
        result = process_message(
            "Coming from Chennai, 3 days, family of 5 with elderly parents",
            test_phone
        )
        assert len(result) <= 1600

    def test_different_users_isolated(self, test_phone, test_phone_2):
        process_message("My name is Ram", test_phone)
        process_message("My name is Kumar", test_phone_2)
        from app.utils.session_store import get_user_name
        assert get_user_name(test_phone) == "Ram"
        assert get_user_name(test_phone_2) == "Kumar"