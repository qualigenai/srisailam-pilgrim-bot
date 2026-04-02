import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.orchestrator import process_message
from app.agents.intent_classifier import classify_intent
from app.multilingual.detector import detect_language

def test_intent_classifier():
    print("\n🧪 Testing Intent Classifier...")
    tests = [
        ("Hi", "greeting"),
        ("Hello", "greeting"),
        ("What time does temple open?", "temple_info"),
        ("How to book darshan?", "booking"),
        ("What is Rudrabhishekam?", "ritual"),
        ("When is Maha Shivaratri?", "festival"),
        ("What is the price of gold?", "unknown"),
    ]
    passed = 0
    for message, expected in tests:
        result = classify_intent(message)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{message}' → {result} (expected: {expected})")
        if result == expected:
            passed += 1
    print(f"\n📊 Intent tests: {passed}/{len(tests)} passed")

def test_language_detector():
    print("\n🧪 Testing Language Detector...")
    tests = [
        ("What time does temple open?", "en"),
        ("గుడి సమయాలు ఏమిటి?", "te"),
        ("मंदिर का समय क्या है?", "hi"),
    ]
    passed = 0
    for message, expected in tests:
        result = detect_language(message)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{message[:30]}' → {result} (expected: {expected})")
        if result == expected:
            passed += 1
    print(f"\n📊 Language tests: {passed}/{len(tests)} passed")

def test_full_pipeline():
    print("\n🧪 Testing Full Pipeline...")
    tests = [
        "Hi",
        "What time does Srisailam temple open?",
        "How to book darshan tickets?",
        "What is the significance of Mallikarjuna?",
        "గుడి సమయాలు ఏమిటి?",
        "मंदिर का समय क्या है?",
        "What is the price of petrol?",
    ]
    for message in tests:
        print(f"\n📩 Input: {message}")
        response = process_message(message, "test_user")
        print(f"🤖 Response: {response[:100]}...")

if __name__ == "__main__":
    test_language_detector()
    test_intent_classifier()
    test_full_pipeline()
    print("\n✅ All tests complete!")