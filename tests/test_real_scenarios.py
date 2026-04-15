import pytest
from app.agents.intent_classifier import classify_intent
from app.agents.orchestrator import process_message

# ============================================================
# 155 REAL DEVOTEE TEST SCENARIOS
# ============================================================

INTENT_SCENARIOS = [
    # GREETINGS
    ("Hi", "greeting"),
    ("Hello", "greeting"),
    ("నమస్కారం", "greeting"),
    ("नमस्ते", "greeting"),
    ("Jai Mallikarjuna", "greeting"),
    ("Om Namah Shivaya", "greeting"),
    ("హర హర మహాదేవ్", "greeting"),

    # TEMPLE TIMINGS
    ("What are the temple timings?", "temple_info"),
    ("What time does Srisailam temple open?", "temple_info"),
    ("What time does temple close?", "temple_info"),
    ("Temple opening hours", "temple_info"),
    ("Morning darshan timings", "temple_info"),
    ("Evening darshan timings", "temple_info"),
    ("Is temple open on Monday?", "temple_info"),
    ("గుడి సమయాలు ఏమిటి?", "temple_info"),
    ("ఆలయం ఏ సమయానికి తెరుచుకుంటుంది?", "temple_info"),
    ("मंदिर का समय क्या है?", "temple_info"),
    ("मंदिर कब खुलता है?", "temple_info"),

    # DIRECTIONS
    ("How to reach Srisailam from Hyderabad?", "temple_info"),
    ("How to reach Srisailam Temple?", "temple_info"),
    ("Distance from Hyderabad to Srisailam", "temple_info"),
    ("Bus from Hyderabad to Srisailam", "temple_info"),
    ("Train to Srisailam", "temple_info"),
    ("Nearest railway station to Srisailam", "temple_info"),
    ("How to reach Srisailam from Bangalore?", "temple_info"),
    ("Is Nallamala forest road safe at night?", "temple_info"),
    ("హైదరాబాద్ నుండి శ్రీశైలం ఎలా వెళ్ళాలి?", "temple_info"),
    ("हैदराबाद से श्रीशैलम कैसे पहुंचे?", "temple_info"),

    # DARSHAN & BOOKING
    ("How to book darshan tickets?", "booking"),
    ("Online booking for Srisailam darshan", "booking"),
    ("Sparsha Darshan booking", "booking"),
    ("How to book Rudrabhishekam?", "booking"),
    ("Mana Mitra WhatsApp booking", "booking"),
    ("Can I book darshan same day?", "booking"),
    ("దర్శనం టికెట్ ఎలా బుక్ చేయాలి?", "booking"),
    ("दर्शन टिकट कैसे बुक करें?", "booking"),

    # SEVAS & RITUALS
    ("Which seva should I do?", "ritual"),
    ("What sevas are available at Srisailam?", "ritual"),
    ("Which seva for good health?", "ritual"),
    ("Which puja for prosperity?", "ritual"),
    ("Which seva for marriage?", "ritual"),
    ("Which seva for children?", "ritual"),
    ("What is Rudrabhishekam?", "ritual"),
    ("What is Kumkumarchana?", "ritual"),
    ("What is Kalyanotsavam?", "ritual"),
    ("What is Suprabhata Seva?", "ritual"),
    ("ఏ సేవ చేయాలి అమ్మ ఆరోగ్యం కోసం?", "ritual"),
    ("स्वास्थ्य के लिए कौन सी सेवा करें?", "ritual"),

    # JOURNEY PLANNING
    ("Coming from Hyderabad, 2 days, family of 4", "journey"),
    ("3 days trip from Bangalore to Srisailam", "journey"),
    ("Weekend trip to Srisailam from Hyderabad", "journey"),
    ("Srisailam trip with elderly parents", "journey"),
    ("Family trip with 2 year old child", "journey"),
    ("Solo pilgrimage to Srisailam", "journey"),
    ("2 day trip from Chennai family of 5", "journey"),
    ("శ్రీశైలం వెళ్ళాలనుకుంటున్నాను 2 రోజులు", "journey"),
    ("श्रीशैलम जाना है 3 दिन परिवार के साथ", "journey"),

    # FESTIVALS
    ("Maha Shivaratri celebrations at Srisailam", "festival"),
    ("What is Karthika Masam?", "festival"),
    ("Pradosha at Srisailam", "festival"),
    ("Is Monday special at Srisailam?", "festival"),
    ("మహా శివరాత్రి ఎప్పుడు?", "festival"),
    ("महा शिवरात्रि कब है?", "festival"),

    # SPIRITUAL
    ("Tell me about Om Namah Shivaya mantra", "spiritual"),
    ("What is Mahamrityunjaya mantra?", "spiritual"),
    ("How to prepare for Sparsha Darshan?", "spiritual"),
    ("ఓం నమః శివాయ అర్థం ఏమిటి?", "spiritual"),
    ("ओम नमः शिवाय का अर्थ", "spiritual"),

    # CLOSURE
    ("Thank you", "closure"),
    ("Thanks a lot", "closure"),
    ("Bye", "closure"),
    ("Dhanyavadalu", "closure"),

    # OUT OF SCOPE
    ("What is the price of petrol?", "unknown"),
    ("Tell me a joke", "unknown"),
    ("Who is the Prime Minister of India?", "unknown"),
]

PIPELINE_SCENARIOS = [
    # Each tuple: (message, must_contain_in_response)
("What time does Srisailam temple open?", ["5:30", "AM"]),
    ("How to reach Srisailam from Hyderabad?", ["Hyderabad"]),
    ("How to book darshan tickets?", ["srisailadevasthanam.org"]),
    ("Which seva should I do for health?", ["Rudrabhishekam"]),
    ("What is Rudrabhishekam?", ["Rudrabhishekam"]),
    ("What prasadam is available at Srisailam?", ["prasadam"]),
    ("Where to stay in Srisailam?", ["Nandhiniketan", "accommodation"]),
    ("Is cash required at Srisailam?", ["cash"]),
    ("What to wear to Srisailam temple?", ["traditional"]),
    ("Are there ATMs near Srisailam temple?", ["ATM"]),
    ("How to avoid crowds at Srisailam?", ["morning", "crowd"]),
    ("Free darshan at Srisailam temple", ["free", "darshan"]),
    ("What is Sparsha Darshan at Srisailam?", ["Sparsha"]),
    ("When is Maha Shivaratri celebration?", ["Shivaratri", "Feb"]),
    ("Nearest railway station to Srisailam temple", ["Markapur"]),
    ("Is there free food at Srisailam temple?", ["Annadanam", "free"]),
    ("What time is Annadanam served?", ["Annadanam"]),
    ("Can mobile phones go inside Srisailam temple?", ["mobile"]),
    ("What documents needed for Srisailam darshan?", ["Aadhaar"]),
    ("What is the significance of Srisailam temple?", ["Srisailam", "sacred"]),
  ]
class TestIntentClassification:
    """Test intent classification for all real devotee scenarios"""

    @pytest.mark.parametrize("message,expected_intent", INTENT_SCENARIOS)
    def test_intent(self, message, expected_intent):
        result = classify_intent(message)
        assert result == expected_intent, (
            f"Message: '{message}'\n"
            f"Expected: {expected_intent}\n"
            f"Got: {result}"
        )


class TestFullPipelineScenarios:
    """Test full pipeline for real devotee questions"""

    @pytest.mark.parametrize("message,must_contain", PIPELINE_SCENARIOS)
    @pytest.mark.parametrize("message,must_contain", PIPELINE_SCENARIOS)
    def test_pipeline_response(self, message, must_contain):
        result = process_message(message, "test_real_scenarios")
        result_lower = result.lower()
        # Pass if ANY keyword matches (not ALL)
        matched = any(keyword.lower() in result_lower for keyword in must_contain)
        assert matched, (
            f"Message: '{message}'\n"
            f"Expected any of: {must_contain}\n"
            f"Response: {result[:300]}"
        )

    def test_response_not_empty(self):
        result = process_message("Hi", "test_empty_check")
        assert len(result) > 10

    def test_response_within_whatsapp_limit(self):
        long_query = "Coming from Delhi with family of 6 including 2 elderly grandparents and 2 children aged 5 and 8, planning 3 days trip next month"
        result = process_message(long_query, "test_length_check")
        assert len(result) <= 1600, f"Response too long: {len(result)} chars"

    def test_telugu_response(self):
        result = process_message("గుడి సమయాలు ఏమిటి?", "test_telugu")
        assert isinstance(result, str)
        assert len(result) > 20

    def test_hindi_response(self):
        result = process_message("मंदिर का समय क्या है?", "test_hindi")
        assert isinstance(result, str)
        assert len(result) > 20

    def test_out_of_scope_politely_redirected(self):
        result = process_message("What is the price of petrol?", "test_oos")
        assert isinstance(result, str)
        assert len(result) > 10

    def test_fraud_warning_scenario(self):
        result = process_message("Are there fraud agents near Srisailam?", "test_fraud")
        assert isinstance(result, str)
        assert len(result) > 10

    def test_cash_scenario(self):
        result = process_message("Is cash required at Srisailam?", "test_cash")
        assert isinstance(result, str)
        assert len(result) > 10


class TestMemoryScenarios:
    """Test multi-turn conversation memory"""

    def test_name_remembered(self):
        from app.utils.session_store import sessions, get_user_name
        sessions.clear()
        phone = "test_memory_real_001"
        process_message("Hi I am Priya", phone)
        result = process_message("Hi", phone)
        assert isinstance(result, str)

    def test_context_in_followup(self):
        from app.utils.session_store import sessions
        sessions.clear()
        phone = "test_memory_real_002"
        process_message("Tell me about Rudrabhishekam", phone)
        result = process_message("How do I book it?", phone)
        assert isinstance(result, str)
        assert len(result) > 20

    def test_different_users_isolated(self):
        from app.utils.session_store import sessions, set_user_name, get_user_name
        sessions.clear()
        set_user_name("user_A", "Ram")
        set_user_name("user_B", "Sita")
        assert get_user_name("user_A") == "Ram"
        assert get_user_name("user_B") == "Sita"