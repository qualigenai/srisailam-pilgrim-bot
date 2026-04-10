import pytest
import time
from app.agents.intent_classifier import classify_intent
from app.rag.hybrid_retriever import search_hybrid

class TestPerformance:

    def test_intent_classification_speed(self):
        start = time.time()
        classify_intent("What time does temple open?")
        elapsed = time.time() - start
        assert elapsed < 5.0

    def test_rag_search_speed(self):
        start = time.time()
        search_hybrid("temple timings", top_k=3)
        elapsed = time.time() - start
        assert elapsed < 3.0

    def test_multiple_intent_classifications(self):
        messages = [
            "Hi", "What time does temple open?",
            "How to book darshan?", "Thank you"
        ]
        start = time.time()
        for msg in messages:
            classify_intent(msg)
        elapsed = time.time() - start
        assert elapsed < 20.0

    def test_response_not_empty(self):
        from app.agents.orchestrator import process_message
        result = process_message("Hi", "perf_test_phone")
        assert len(result) > 0

    def test_rag_returns_quickly(self):
        queries = [
            "temple timings",
            "Rudrabhishekam",
            "how to reach Srisailam"
        ]
        for query in queries:
            start = time.time()
            results = search_hybrid(query, top_k=3)
            elapsed = time.time() - start
            assert elapsed < 3.0
            assert len(results) > 0