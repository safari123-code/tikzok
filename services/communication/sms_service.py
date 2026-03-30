# ---------------------------
# Telnyx SMS Service (Production Ready)
# ---------------------------

import os
import telnyx


class SMSService:

    @staticmethod
    def send_sms(to_number: str, message: str) -> dict:

        api_key = os.getenv("TELNYX_API_KEY")
        sender = os.getenv("TELNYX_SMS_FROM")

        if not api_key:
            raise RuntimeError("TELNYX_API_KEY not configured")

        if not sender:
            raise RuntimeError("TELNYX_SMS_FROM not configured")

        telnyx.api_key = api_key

        try:
            response = telnyx.Message.create(
                from_=sender,
                to=to_number,
                text=message
            )

            # ✅ return propre (pas l’objet brut)
            return {
                "success": True,
                "message_id": response.id,
                "to": to_number
            }

        except Exception as e:
            # ⚠️ pas de print brut en prod
            return {
                "success": False,
                "error": str(e)
            }