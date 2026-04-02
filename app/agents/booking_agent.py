import logging

logger = logging.getLogger(__name__)

BOOKING_MESSAGE = """🙏 For all bookings at Srisailam temple:

📱 *Mana Mitra WhatsApp:*
Send Hi to 9552300009

🌐 *Official Website:*
srisailadevasthanam.org

📞 *Temple Office:*
08524-288888 / 08524-288889

You can book:
- Darshan tickets (Sarva / Special / Sparsha)
- Seva tickets (Rudrabhishekam, Abhishekam etc.)
- Accommodation (Nandhiniketan, guest houses)
- Paroksha Seva (remote seva booking)
- e-Hundi (online donation)

Aadhaar card is mandatory for all bookings. 🕉️"""

def handle_booking() -> str:
    logger.info("🎫 Handling booking query")
    return BOOKING_MESSAGE