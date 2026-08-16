import datetime, hashlib, base64, hmac, os


keys = {"tg": os.getenv("TIGOR_TG_SECRET")}

if not keys["tg"] or len(keys["tg"]) < 16:
    raise Exception("Key not found TIGOR_TG_SECRET")


# Token format for v1: user_id|priority|max_daily_messages|max_tokens|valid_until|version|authority|signature
def read_token_v1(token):
    if len(token) > 1000:
        return None
    
    parts = token.split("|", 7)

    if len(parts) != 8:
        return None
    
    user_id, priority, max_daily_messages, max_tokens, valid_until, version, authority, signature = parts

    try:
        signature_raw = base64.urlsafe_b64decode(signature)
    except Exception:
        return None
    
    today = datetime.date.today().strftime("%Y-%m-%d")

    if valid_until < today or version != "v1" or authority not in keys:
        return None
    
    message = user_id + "|" + priority + "|" + max_daily_messages + "|" + max_tokens + "|" + valid_until + "|" + version + "|" + authority

    correct_signature_raw = hmac.new(keys[authority].encode(), message.encode(), hashlib.sha256).digest()

    if not hmac.compare_digest(signature_raw, correct_signature_raw):
        return None

    return {"user_id": user_id, "priority": int(priority), "max_daily_messages": int(max_daily_messages), "max_tokens": int(max_tokens)}
