import logging

logger = logging.getLogger(__name__)

FALLBACK_MESSAGES = {
    "en": """🙏 Sorry, I couldn't process your request right now.

Please try again or contact us:
📞 08524-288888
🌐 srisailadevasthanam.org
📱 Mana Mitra: 9552300009""",

    "te": """🙏 క్షమించండి, మీ అభ్యర్థనను ప్రాసెస్ చేయలేకపోయాను.

దయచేసి మళ్ళీ ప్రయత్నించండి లేదా సంప్రదించండి:
📞 08524-288888
🌐 srisailadevasthanam.org
📱 మన మిత్ర: 9552300009""",

    "hi": """🙏 क्षमा करें, मैं अभी आपका अनुरोध संसाधित नहीं कर सका।

कृपया पुनः प्रयास करें या संपर्क करें:
📞 08524-288888
🌐 srisailadevasthanam.org
📱 मन मित्र: 9552300009"""
}

def get_fallback_message(lang: str = "en") -> str:
    return FALLBACK_MESSAGES.get(lang, FALLBACK_MESSAGES["en"])

def get_unknown_message(lang: str = "en") -> str:
    messages = {
        "en": """🙏 I am your Srisailam Pilgrim Guide!

I can help with:
- Temple timings & darshan
- How to reach Srisailam
- Sevas & rituals
- Festivals & auspicious days
- Accommodation

What would you like to know? 🕉️""",

        "te": """🙏 నేను మీ శ్రీశైలం యాత్రా గైడ్!

నేను సహాయం చేయగలను:
- గుడి సమయాలు & దర్శనం
- శ్రీశైలం ఎలా చేరుకోవాలి
- సేవలు & పూజలు
- పండుగలు & శుభ దినాలు
- వసతి సౌకర్యాలు

మీకు ఏమి తెలుసుకోవాలి? 🕉️""",

        "hi": """🙏 मैं आपका श्रीशैलम तीर्थ यात्रा गाइड हूं!

मैं मदद कर सकता हूं:
- मंदिर समय और दर्शन
- श्रीशैलम कैसे पहुंचें
- सेवाएं और पूजा
- त्योहार और शुभ दिन
- आवास सुविधाएं

आप क्या जानना चाहते हैं? 🕉️"""
    }
    return messages.get(lang, messages["en"])