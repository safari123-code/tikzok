import secrets
from services.communication.email_service import EmailService
from services.communication.otp_service import OtpService


class EmailOTPService:

    # ---------------------------
    # Generate OTP code (6 chiffres sécurisé)
    # ---------------------------
    @staticmethod
    def generate_code() -> str:
        return str(secrets.randbelow(9000) + 1000)

    # ---------------------------
    # Send verification email
    # ---------------------------
    @staticmethod
    def send_verification(email: str):

        code = EmailOTPService.generate_code()

        # 🔐 IMPORTANT (sinon verify cassé)
        OtpService.store_otp("email", email, code)

        subject = "Code de vérification Tikzok"

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

        text = f"""Code de vérification Tikzok

Votre code : {code}

Ce code expire dans 5 minutes.
"""

        EmailService.send_email(
            to_email=email,
            subject=subject,
            html=html,
            text=text
        )

        # ⚠️ OK pour test seulement
        return code