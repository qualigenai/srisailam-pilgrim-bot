import pytest
from app.utils.session_store import (
    get_session, set_user_language, get_user_language,
    add_to_history, get_history, get_history_as_text,
    set_user_name, get_user_name, clear_session
)

class TestSessionStore:

    def test_new_session_created(self, test_phone):
        session = get_session(test_phone)
        assert session is not None
        assert session["phone"] == test_phone

    def test_language_set_get(self, test_phone):
        set_user_language(test_phone, "te")
        assert get_user_language(test_phone) == "te"

    def test_default_language_english(self, test_phone):
        assert get_user_language(test_phone) == "en"

    def test_add_history(self, test_phone):
        add_to_history(test_phone, "user", "Hello")
        history = get_history(test_phone)
        assert len(history) == 1
        assert history[0]["message"] == "Hello"
        assert history[0]["role"] == "user"

    def test_history_accumulates(self, test_phone):
        add_to_history(test_phone, "user", "Message 1")
        add_to_history(test_phone, "bot", "Response 1")
        add_to_history(test_phone, "user", "Message 2")
        history = get_history(test_phone)
        assert len(history) == 3

    def test_history_as_text(self, test_phone):
        add_to_history(test_phone, "user", "Hi")
        add_to_history(test_phone, "bot", "Welcome!")
        text = get_history_as_text(test_phone)
        assert "Hi" in text
        assert "Welcome!" in text

    def test_set_get_name(self, test_phone):
        set_user_name(test_phone, "Ram")
        assert get_user_name(test_phone) == "Ram"

    def test_clear_session(self, test_phone):
        set_user_name(test_phone, "Ram")
        clear_session(test_phone)
        assert get_user_name(test_phone) is None

    def test_history_limit(self, test_phone):
        for i in range(15):
            add_to_history(test_phone, "user", f"Message {i}")
        history = get_history(test_phone)
        assert len(history) <= 10


class TestMemoryAgent:

    def test_extract_name_from_intro(self):
        from app.agents.memory_agent import extract_name_from_message
        result = extract_name_from_message("My name is Ram")
        assert result is not None
        assert "Ram" in result

    def test_no_name_in_message(self):
        from app.agents.memory_agent import extract_name_from_message
        result = extract_name_from_message("What time does temple open?")
        assert result is None

    def test_followup_detection(self):
        from app.agents.memory_agent import is_follow_up
        history = "Bot: Rudrabhishekam takes 30-45 minutes"
        assert is_follow_up("and then what", history) == True

    def test_not_followup_empty_history(self):
        from app.agents.memory_agent import is_follow_up
        assert is_follow_up("What time does temple open?", "") == False