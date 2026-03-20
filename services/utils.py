# ---------------------------
# Mask phone
# ---------------------------
def mask_phone(phone: str, is_super_admin: bool = False):

    if not phone:
        return "—"

    if is_super_admin:
        return phone  # 👑 toi → full

    # masque: +33751234567 → +3375****567
    if len(phone) < 8:
        return phone

    return phone[:5] + "****" + phone[-3:]