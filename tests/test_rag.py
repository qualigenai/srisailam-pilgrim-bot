import pytest
from app.rag.hybrid_retriever import search_hybrid
from app.rag.qa_chain import answer_question

class TestHybridRetriever:

    def test_returns_results(self):
        results = search_hybrid("temple timings", top_k=3)
        assert len(results) > 0

    def test_returns_strings(self):
        results = search_hybrid("Rudrabhishekam", top_k=3)
        assert all(isinstance(r, str) for r in results)

    def test_temple_timings_query(self):
        results = search_hybrid("What time does temple open?", top_k=3)
        assert len(results) > 0
        combined = " ".join(results).lower()
        assert "5:30" in combined or "temple" in combined

    def test_seva_query(self):
        results = search_hybrid("Rudrabhishekam seva", top_k=3)
        combined = " ".join(results).lower()
        assert "rudrabhishekam" in combined or "abhishekam" in combined

    def test_travel_query(self):
        results = search_hybrid("How to reach Srisailam from Hyderabad", top_k=3)
        combined = " ".join(results).lower()
        assert "hyderabad" in combined or "km" in combined

    def test_festival_query(self):
        results = search_hybrid("Maha Shivaratri at Srisailam", top_k=3)
        combined = " ".join(results).lower()
        assert "shivaratri" in combined or "festival" in combined

    def test_top_k_respected(self):
        results = search_hybrid("temple", top_k=2)
        assert len(results) <= 2

    def test_accommodation_query(self):
        results = search_hybrid("accommodation near Srisailam", top_k=3)
        assert len(results) > 0


class TestQAChain:

    def test_answer_temple_timing(self):
        result = answer_question("What time does Srisailam temple open?")
        assert isinstance(result, str)
        assert len(result) > 20
        assert "5:30" in result or "AM" in result or "temple" in result.lower()

    def test_answer_rudrabhishekam(self):
        result = answer_question("What is Rudrabhishekam?")
        assert isinstance(result, str)
        assert len(result) > 20

    def test_answer_out_of_scope(self):
        result = answer_question("What is the capital of France?")
        assert isinstance(result, str)
        assert "srisailadevasthanam.org" in result or "don't have" in result.lower()

    def test_answer_returns_string(self):
        result = answer_question("How to reach Srisailam?")
        assert isinstance(result, str)
        assert len(result) > 10