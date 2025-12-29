from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch, UrlContext
from pydantic import BaseModel, Field
from domain.post import Post
from env import GEMINI_API_KEY, GEMINI_MODEL


class MatchResult(BaseModel):
    signal: int = Field(description="How important this information is. 1 being the least, 10 the highest.")
    summary: str = Field(description="A short summary that contains all relevant information in the text with no other information. This will be used for further processing to find links between data sources.")
    financial: bool = Field(description="Should a trade happen based on this information.")
    alertable: bool = Field(description="Should a notification be sent about this to the user if this is noteworthy news.")


class GeminiAnalyst:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = GEMINI_MODEL

    def analyze(self, title, summary, linked_data):
        prompt = f"""
You are a cynicism-aware Intelligence Analyst. 
Your goal is to separate actual high-signal news from satire, rage-bait, and tech-industry sarcasm. Content you analyse may come from archives, analyse it as if it were the original source with no knowledge of the archive.

CORE DIRECTIVE:
Before classifying ANY item as "High Signal," you must first pass it through a "Satire Filter."

PHASE 1: SATIRE & ABSURDITY CHECK
Ask yourself:
1. Is the source a known satirical outlet? (e.g., The Onion, Hard Drive, Daily Mash, New Yorker Borowitz Report).
2. Is the headline "Too Perfect"? (e.g., "Developer Deletes Production Database to Fix Imposter Syndrome").
3. Is it logically impossible or framing a trivial tech grievance as a global catastrophe?

If YES to any of the above:
- MARK AS SIGNAL 0
- OUTPUT FINANCIAL AND ALERTABLE TO FALSE
- RETURN "N/A - NOISE" AS THE SUMMARY

PHASE 2: SIGNAL GRADING (Only if Phase 1 is passed)
- Kinetic: War, troop movements, physical infrastructure failure, drone strikes, bombings, terrorism. (Signal 8-10)
- Economic: Central bank rates, bankruptcy, new trade laws, supply chain halts. (Signal 7-10)
- Tech: Zero-day exploits (CVEs), Model Weight releases, massive breaches. (Signal 7-10)
These categories are not exclusive but are given as relevant examples.

NOISE (Signal 0-4) -> DISCARD:
- Opinion pieces / "Hot Takes" / Think-pieces.
- Tutorials ("How to build X").
- General complaints about software complexity.
- "Show HN" projects that are minor tools.

OUTPUT FORMAT, JSON ONLY:
{{
    "signal": <int>,
    "financial": <bool>,
    "alertable": <bool>,
    "summary": "<concise_text>"
}}
signal: 1-10 (how important this information is. 1 being the least, 10 the highest)
financial: true/false (should a trade happen based on this information)
summary: text (a summary that contains all relevant information in the text ONLY. This will be used for further processing without the source so make sure to inlcude all relevant information that future analysis may need. Further analysis will be conducted for linking events together and finding large scale correlations. For efficiently, make sure to omit any and all non-relavant infomration. Amounts and numbers may be useful for quantising the scale of the event. Be consise but complete.)
alertable: true/false
CRITERIA FOR ALERTABLE TRUE:
1. IMMINENT DANGER: A kinetic event, cyberattack, or financial crash is happening NOW or will happen within 48 hours.
2. ACTION REQUIRED: The user must physically or digitally do something (e.g., "Patch this CVE," "Sell this asset," "Cancel travel to X").
3. NOVELTY: A massive, unexpected event (e.g., "Prime Minister Resigns," "Google releases GPT-5 level model").
CRITERIA FOR ALERTABLE FALSE (Even if High Signal):
- Announcements of future conferences, meetings, or panels (e.g., "Speakers announced for a conference").
- Release of "Guidance," "Best Practices," "Whitepapers," or "Strategy Documents."
- Formation of new "partnerships," "alliances," or "working groups" without immediate action.
- "Calls for action" or politicians "urging" something to happen.

CONTEXT:
Title and content are the title and content of the RSS feed. Linked data content contains data from links within the RSS feed.

--- TITLE ---
{title}
--- CONTENT ---
{summary}
--- LINKED DATA CONTENT ---
{linked_data}
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": MatchResult.model_json_schema(),
            }
        )
        try:
            result = MatchResult.model_validate_json(response.text or "")
            return result
        except Exception as e:
            print(f"Gemini Error: {e}")
            print(response.text)
            return None


    def analyze_post(self, post: Post):
        prompt = f"""
You are a cynicism-aware Intelligence Analyst. 
Your goal is to separate actual high-signal news from satire, rage-bait, and tech-industry sarcasm. Content you analyse are posts from bluesky and mastodon seconds after posting.

CORE DIRECTIVE:
Before classifying ANY item as "High Signal," you must first pass it through a "Satire Filter."

PHASE 1: SATIRE & ABSURDITY CHECK
Ask yourself:
1. Is the source a known satirical outlet? (e.g., The Onion, Hard Drive, Daily Mash, New Yorker Borowitz Report).
2. Is the headline "Too Perfect"? (e.g., "Developer Deletes Production Database to Fix Imposter Syndrome").
3. Is it logically impossible or framing a trivial tech grievance as a global catastrophe?

If YES to any of the above:
- MARK AS SIGNAL 0
- OUTPUT FINANCIAL AND ALERTABLE TO FALSE
- RETURN "N/A - NOISE" AS THE SUMMARY

PHASE 2: SIGNAL GRADING (Only if Phase 1 is passed)
- Kinetic: War, troop movements, physical infrastructure failure, drone strikes, bombings, terrorism. (Signal 8-10)
- Economic: Central bank rates, bankruptcy, new trade laws, supply chain halts. (Signal 7-10)
- Tech: Zero-day exploits (CVEs), Model Weight releases, massive breaches. (Signal 7-10)
These categories are not exclusive but are given as relevant examples.

NOISE (Signal 0-4) -> DISCARD:
- Opinion pieces / "Hot Takes" / Think-pieces.
- Tutorials ("How to build X").
- General complaints about software complexity.


OUTPUT FORMAT, JSON ONLY:
{{
    "signal": <int>,
    "financial": <bool>,
    "alertable": <bool>,
    "summary": "<concise_text>"
}}
signal: 1-10 (how important this information is. 1 being the least, 10 the highest)
financial: true/false (should a trade happen based on this information)
summary: text (a summary that contains all relevant information in the text ONLY. This will be used for further processing without the source so make sure to inlcude all relevant information that future analysis may need. Further analysis will be conducted for linking events together and finding large scale correlations. For efficiently, make sure to omit any and all non-relavant infomration. Amounts and numbers may be useful for quantising the scale of the event. Be consise but complete.)
alertable: true/false
CRITERIA FOR ALERTABLE TRUE:
1. IMMINENT DANGER: A kinetic event, cyberattack, or financial crash is happening NOW or will happen within 48 hours.
2. ACTION REQUIRED: The user must physically or digitally do something (e.g., "Patch this CVE," "Sell this asset," "Cancel travel to X").
3. NOVELTY: A massive, unexpected event (e.g., "Prime Minister Resigns," "Google releases GPT-5 level model").
CRITERIA FOR ALERTABLE FALSE (Even if High Signal):
- Announcements of future conferences, meetings, or panels (e.g., "Speakers announced for a conference").
- Release of "Guidance," "Best Practices," "Whitepapers," or "Strategy Documents."
- Formation of new "partnerships," "alliances," or "working groups" without immediate action.
- "Calls for action" or politicians "urging" something to happen.

--- AUTHOR ---
{post.author_display_name}
--- CONTENT ---
{post.content}
--- LINKS ---
{post.links}
"""

        # tools = [
        #     {"url_context": {}},
        # ]
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=MatchResult.model_json_schema(),
                # tools=tools
            )
        )
        try:
            result = MatchResult.model_validate_json(response.text or "")
            return result
        except Exception as e:
            print(f"Gemini Error: {e}")
            print(response.text)
            return None
