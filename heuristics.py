from domain.post import Post

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
    "thehardtimes.net",
    "amzn.to",
    "amazon.com",
    "amazon.co.uk",
    "rss-parrot.net",
    "newsbeep.com",
    "newsbeep.org",
    "washingtonpost.com",
}

SHORTLIST_ACCOUNTS = {
    # BlueSky
    "did:plc:6ofscwmf6hva6ega2a5jirq7", # hunterbrook media
    "did:plc:sb54dpdfefflykmf5bcfvr7t", # bellingcat
    "did:plc:oaektkwkglhxs2zlts4nzuvr", # shayan86.bsky.social
    "did:plc:c6hdm36q5qqcf5puaao3v33m", # acleddata.bsky.social
    "did:plc:uewxgchsjy4kmtu7dcxa77us", # bloomberg
    "did:plc:xraomsuf6pvh7r2cqtdwhkvm", # swiftonsecurity.com
    "did:plc:anssft5emdfb2sjnjyeqnprh", # alisonkilling.bsky.social
    "did:plc:73234535z57357466535", # FT
    "did:plc:idwhjzs5boatwv4zxwwcjk5i", # malwaretech.com
    
    # Mastodon
    # @mastodon.social users have no @mastodon.social in tag as we are on their fedi
    "EUVD_Bot",
}

IGNORE_ACCOUNTS = {
    # BlueSky
    "did:plc:2kzaomqz4kto7ii5sry7sgfs",
    # Mastodon
    "newsbeep@newsbeep.org",
}

KEYWORDS = {
    # --- KINETIC / MILITARY (Troops, Strikes, War) ---
    # English
    "explosion", "missile", "airstrike", "troops", "invaded", "coup", 
    "rioting", "emergency declared", "breaking", "invades", "invade"
    "peace", "capture", "forces", "raid",
    # Ukrainian
    "вибух", "ракетний удар", "повітряна тривога", "вторгнення", 
    "обстріл", "ЗСУ", "втрати", "загинули", "наступ", "фронт", 
    "мобілізація", "евакуація", "ядерна загроза", "збито", "артилерія",
    # Russian
    "взрыв", "ракетный удар", "воздушная тревога", "вторжение", 
    "обстрел", "потери", "погибли", "наступление", "фронт", 
    "мобилизация", "эвакуация", "ядерная угроза", "сбито", "артиллерия",
    # Hebrew
    "פיצוץ", "אזעקת צבע אדום", "מלחמה", "טילים", "רקטות", 
    "נפגעים", "הרוגים", "צה״ל", "חדירת מחבלים", "תקיפה אווירית", 
    "כיפת ברזל", "פיגוע", "חיסול", "הסלמה", "מילואים",
    # --- FINANCIAL (Collapse, Sanctions, Crisis) ---
    # English
    "bankrupt", "insolvent", "crash", "shares", "stock market",
    "stocks", "bankruptcies", "bankruptcy",
    # Ukranian
    "дефолт", "банкрутство", "інфляція", "санкції", "обвал", 
    "курс долара", "нацбанк", "девальвація", "заморожені активи"
    # Russain
    "дефолт", "банкротство", "инфляция", "санкции", "обвал", 
    "курс рубля", "центробанк", "девальвация", "замороженные активы",
    # Hebrew
    "פשיטת רגל", "אינפלציה", "קריסה כלכלית", "סנקציות", "בורסה", 
    "העלאת ריבית", "פיחות", "גרעון", "מיתון", "שוק ההון",
    # --- CYBER / TECH (Breaches, Hacks, CVEs) ---
    # English
    "cve", "zero-day", "zero day", "breach", "hacks", "hacked", "anon", 
    "hacking", "leak", "password", "passwords", "infosec",
    "privacy", "Cybersecurity"
    # Ukranian
    "кібератака", "злам", "витік даних", "хакери", "ddos", 
    "вірус", "фішинг", "вразливість",
    # Russain
    "кибератака", "взлом", "утечка данных", "хакеры", "ddos", 
    "вирус", "фишинг", "уязвимость",
    # Hebrew
    "מתקפת סייבר", "פריצה", "דליפת מידע", "האקרים", "נוזקה", 
    "כופרה", "פישינג", "חולשת אבטחה",
}

IGNORE_KEYWORDS = {
    "opinion:", "satire", "humor", "cartoon", "ask hn:", "tell hn:",
    "#ad", "#amazon", "#memes", "breaking bad", "#crypto", "#commission",
    "#digtaldrawing", "#art", "#gay", "leaky", "WIP", "star wars",
    "#bdsm", "#bondage", "kink", "#selfship", "#yume", "#zzz", 
    "zenlesszonezero", "#poetry", "fireren", "#horny",
    # Commercial / Spam / Crypto
    "#sponsored", "#partner", "giveaway", "nft", "web3", "airdrop", 
    "affiliate", "promo", "discount", "dropshipping",
    # Expanded Art / Fandom / Gacha
    "fanart", "fanfic", "cosplay", "vtuber", "gacha", "genshin", 
    "honkai", "star rail", "waifu", "oc", "original character",
    "commissions open", "sketch", "doodle", "ych", "adoptable",
    "Wordle", "ffxiv",
    # Social Noise / Engagement Bait
    "thread 🧵", "follow for more", "link in bio", "hot take",
    "sesame street", "the muppet", "booksky",
    # Broad NSFW
    "nsfw", "18+", "lewd", "onlyfans", "porn", "hentai", "linktr.ee",
    "e926"
}

def is_obvious_noise(title: str, url: str) -> bool:
    if any(blocked in url.lower() for blocked in IGNORE_DOMAINS):
        print(f"🚫 SKIPPING (Blocked Domain): {title}")
        return True
        
    if any(kw in title.lower() for kw in IGNORE_KEYWORDS):
        print(f"🚫 SKIPPING (Keyword): {title}")
        return True

    return False

def should_process_post(post: Post) -> bool:
    if post.author_id in SHORTLIST_ACCOUNTS:
        return True
    if post.author_id in IGNORE_ACCOUNTS:
        return False
    
    for domain in IGNORE_DOMAINS:
        if domain in post.url.lower():
            return False
        for link in post.links:
            if domain in link.lower():
                return False
    
    if any(kw in post.content.lower() for kw in IGNORE_KEYWORDS):
        return False
    
    if any(kw in post.content.lower() for kw in KEYWORDS):
        return True
    
    return False