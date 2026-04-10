import pytest
from app.agents.journey_planner_agent import (
    create_itinerary, needs_more_info, extract_journey_details
)

class TestJourneyDetails:

    def test_extract_from_city(self):
        details = extract_journey_details(
            "Coming from Hyderabad, 2 days, family of 4"
        )
        assert details.get("FROM", "").lower() in ["hyderabad", "unknown"] or "hyderabad" in str(details).lower()

    def test_extract_days(self):
        details = extract_journey_details("3 days trip to Srisailam")
        assert "3" in str(details)

    def test_needs_more_info_vague(self):
        assert needs_more_info("I want to visit Srisailam") == True

    def test_needs_more_info_complete(self):
        result = needs_more_info(
            "Coming from Hyderabad, 2 days, family of 4"
        )
        assert result == False

    def test_needs_more_info_with_days(self):
        result = needs_more_info("I want to visit for 2 days")
        assert isinstance(result, bool)


class TestItineraryCreation:

    def test_itinerary_returns_string(self):
        result = create_itinerary(
            "Coming from Hyderabad, 2 days, family of 4",
            "test_phone"
        )
        assert isinstance(result, str)

    def test_itinerary_under_1500_chars(self):
        result = create_itinerary(
            "Coming from Hyderabad, 3 days, family of 5",
            "test_phone"
        )
        assert len(result) <= 1500

    def test_itinerary_contains_booking(self):
        result = create_itinerary(
            "Coming from Hyderabad, 2 days",
            "test_phone"
        )
        assert "srisailadevasthanam.org" in result or "9552300009" in result

    def test_itinerary_contains_emoji(self):
        result = create_itinerary(
            "Coming from Chennai, 2 days",
            "test_phone"
        )
        assert "🙏" in result or "🛕" in result or "📱" in result

    def test_telugu_journey(self):
        result = create_itinerary(
            "హైదరాబాద్ నుండి 2 రోజులు కుటుంబంతో",
            "test_phone"
        )
        assert isinstance(result, str)
        assert len(result) > 50