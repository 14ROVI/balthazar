IGNORE_DOMAINS = {
    "theonion.com",
    "hard-drive.net",
    "dailymash.co.uk",
    "newyorker.com",
    "duffelblog.com",
    "babylonbee.com",
    "reductress.com",
    "medium.com",
    "substack.com",
    "youtube.com",
}

IGNORE_KEYWORDS = {
    "opinion:", 
    "satire", 
    "humor", 
    "cartoon",
    "ask hn:",
    "tell hn:",
}

def is_obvious_noise(title: str, url: str) -> bool:
    if any(blocked in url.lower() for blocked in IGNORE_DOMAINS):
        print(f"🚫 SKIPPING (Blocked Domain): {title}")
        return True
        
    if any(kw in title.lower() for kw in IGNORE_KEYWORDS):
        print(f"🚫 SKIPPING (Keyword): {title}")
        return True

    return False