# users/utils.py
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_sms(phone_number, message):
    """
    Send SMS via Twilio or print to terminal based on settings.
    
    Settings (via environment variables):
    - TWILIO_ENABLED=False: Print to terminal (for testing)
    - TWILIO_ENABLED=True: Send via Twilio (for production/mobile deployment)
    """
    
    twilio_enabled = getattr(settings, 'TWILIO_ENABLED', False)
    
    if not twilio_enabled:
        # Development/Testing mode - Print OTP to terminal
        print("\n" + "="*70)
        print("📱 SMS VERIFICATION (CONSOLE MODE)")
        print("="*70)
        print(f"📞 TO: {phone_number}")
        print(f"📝 MESSAGE: {message}")
        print("="*70 + "\n")
        logger.info(f"[CONSOLE SMS] To: {phone_number} | Message: {message}")
        return True
    
    else:
        # Production mode - Send via Twilio
        try:
            from twilio.rest import Client
            
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
            
            if not all([account_sid, auth_token, from_number]):
                raise ValueError("Twilio credentials not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in .env")
            
            client = Client(account_sid, auth_token)
            
            twilio_message = client.messages.create(
                body=message,
                from_=from_number,
                to=phone_number
            )
            
            logger.info(f"[TWILIO SMS] Sent to {phone_number} | SID: {twilio_message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"[TWILIO SMS] Failed to send to {phone_number}: {str(e)}")
            raise e
