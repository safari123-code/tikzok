# ---------------------------
# Telnyx SMS Service
# ---------------------------

import os
import telnyx


class SMSService:

    @staticmethod
    def send_sms(to_number: str, message: str):

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

            return response

        except Exception as e:

            print("TELNYX SMS ERROR:", e)
            raise