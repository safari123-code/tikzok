# ---------------------------
# Email Service (Amazon SES)
# ---------------------------

import boto3
import os
from datetime import datetime


class EmailService:

    # ---------------------------
    # SES Client
    # ---------------------------
    client = boto3.client(
        "ses",
        region_name=os.getenv("AWS_REGION"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

    # ---------------------------
    # Generic email sender
    # ---------------------------
    @staticmethod
    def send_email(to_email: str, subject: str, html: str, text: str = ""):

        try:

            EmailService.client.send_email(
                Source=os.getenv("SES_FROM_EMAIL"),
                Destination={
                    "ToAddresses": [to_email]
                },
                Message={
                    "Subject": {
                        "Data": subject,
                        "Charset": "UTF-8"
                    },
                    "Body": {
                        "Html": {
                            "Data": html,
                            "Charset": "UTF-8"
                        },
                        "Text": {
                            "Data": text or "Tikzok notification",
                            "Charset": "UTF-8"
                        }
                    }
                },
            )

        except Exception as e:
            print("SES email error:", e)

    # ---------------------------
    # Payment success email
    # ---------------------------
    @staticmethod
    def send_payment_success(email: str, payload: dict, phone: str | None = None):

        amount = payload.get("amount")
        reference = payload.get("reference")
        order_number = payload.get("orderNumber")
        date = payload.get("date")

        fee = "0.00"
        total = amount
        year = datetime.now().year

        subject = f"Recharge confirmée - {reference}"

        html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
</head>

<body style="margin:0;background:#0e1117;font-family:Arial,Helvetica,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="padding:30px 0;">
<tr>
<td align="center">

<table width="100%" cellpadding="0" cellspacing="0"
style="max-width:520px;background:#111827;border-radius:14px;padding:30px;color:white;">

<tr>
<td style="font-size:28px;font-weight:bold;color:#00d1c1;">
Tikzok
</td>

<td style="text-align:right;font-size:13px;color:#9ca3af;">
Référence : {reference}
</td>
</tr>

<tr><td colspan="2" style="height:25px"></td></tr>

<tr>
<td colspan="2" style="font-size:22px;font-weight:bold;text-align:center;">
Votre recharge a été envoyée
</td>
</tr>

<tr>
<td colspan="2" style="text-align:center;color:#9ca3af;padding-top:6px;">
Livré instantanément ⚡
</td>
</tr>

<tr><td colspan="2" style="height:30px"></td></tr>

<tr>
<td colspan="2">

<table width="100%" style="background:#0f172a;border-radius:12px;padding:20px;">

<tr>
<td style="color:#9ca3af;">Date :</td>
<td style="text-align:right;">{date}</td>
</tr>

<tr><td style="height:8px"></td></tr>

<tr>
<td style="color:#9ca3af;">Numéro :</td>
<td style="text-align:right;">{phone or ""}</td>
</tr>

<tr><td style="height:8px"></td></tr>

<tr>
<td style="color:#9ca3af;">Produit :</td>
<td style="text-align:right;">Recharge mobile</td>
</tr>

<tr><td style="height:20px"></td></tr>

<tr>
<td style="color:#9ca3af;">Montant :</td>
<td style="text-align:right;">{amount} €</td>
</tr>

<tr><td style="height:6px"></td></tr>

<tr>
<td style="color:#9ca3af;">Frais :</td>
<td style="text-align:right;">{fee} €</td>
</tr>

<tr><td style="height:10px"></td></tr>

<tr>
<td style="font-weight:bold;">Total :</td>
<td style="text-align:right;font-weight:bold;font-size:18px;">
{total} €
</td>
</tr>

</table>

</td>
</tr>

<tr><td colspan="2" style="height:30px"></td></tr>

<tr>
<td colspan="2" align="center">

<a href="https://tikzok.com"
style="background:#b4ff00;color:black;padding:14px 26px;
text-decoration:none;border-radius:30px;font-weight:bold;display:inline-block;">
Envoyer une autre recharge
</a>

</td>
</tr>

<tr><td colspan="2" style="height:25px"></td></tr>

<tr>
<td colspan="2" style="text-align:center;color:#9ca3af;font-size:12px;">
Besoin d'aide ? Contactez support@tikzok.com
</td>
</tr>

<tr>
<td colspan="2" style="text-align:center;color:#6b7280;font-size:11px;padding-top:10px;">
© {year} Tikzok
</td>
</tr>

</table>

</td>
</tr>
</table>

</body>
</html>
"""

        EmailService.send_email(
            to_email=email,
            subject=subject,
            html=html
        )