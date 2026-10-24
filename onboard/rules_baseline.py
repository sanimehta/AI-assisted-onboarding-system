from .generate import ALL_DOCS

def rules_extract(email):
    low = email.lower()
    docs = [d for d in ALL_DOCS if d in low]
    fmt = next((f for f in ('csv', 'txt', 'xml') if f in low), None)
    if any(p in low for p in ('we host', 'our ftp', 'host the ftp', 'our it', 'ourselves')):
        owner = 'customer'
    elif any(p in low for p in ('host a folder', 'do not have an ftp', 'your side', 'you host')):
        owner = 'us'
    else:
        owner = None
    return {'docs': docs, 'format': fmt, 'ftp_owner': owner}