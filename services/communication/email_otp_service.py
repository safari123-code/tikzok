# ---------------------------
# Email OTP Service
# ---------------------------

import random
from services.communication.email_service import EmailService


class EmailOTPService:

    # ---------------------------
    # Generate OTP code
    # ---------------------------
    @staticmethod
    def generate_code() -> str:
        return str(random.randint(1000, 9999))

    # ---------------------------
    # Send verification email
    # ---------------------------
    @staticmethod
    def send_verification(email: str):

        code = EmailOTPService.generate_code()

        subject = "Code de vérification Tikzok"

        # HTML email
        html = f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial;background:#f4f6f8;padding:30px;">

<table width="100%" style="max-width:480px;margin:auto;background:white;border-radius:10px;padding:30px;">

<tr>
<td style="text-align:center;font-size:24px;font-weight:bold;">
Tikzok
</td>
</tr>

<tr><td style="height:20px"></td></tr>

<tr>
<td style="text-align:center;font-size:18px;">
Code de vérification
</td>
</tr>

<tr><td style="height:20px"></td></tr>

<tr>
<td style="text-align:center;font-size:32px;font-weight:bold;letter-spacing:6px;">
{code}
</td>
</tr>

<tr><td style="height:20px"></td></tr>

<tr>
<td style="text-align:center;color:#666;font-size:14px;">
Ce code expire dans 5 minutes
</td>
</tr>

</table>

</body>
</html>
"""

        # Text fallback
        text = f"""
Code de vérification Tikzok

Votre code :

{code}

Ce code expire dans 5 minutes.
"""

        EmailService.send_email(
            to_email=email,
            subject=subject,
            html=html,
            text=text
        )

        return code