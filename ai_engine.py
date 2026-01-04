from google import genai
from google.genai.types import GenerateContentConfig
from pydantic import BaseModel, Field
from domain.post import Post
from datetime import datetime
from typing import List
import json
from db import EventRow
from env import GEMINI_API_KEY, GEMINI_MODEL



class EventsResult(BaseModel):
    new_events: List[NewEvent]
    updated_summaries: List[UpdatedSummary]
    updated_sources: List[UpdatedSources]
    
class NewEvent(BaseModel):
    summary: str = Field(..., description="Concise summary of the fact content of the event.")
    signal: int = Field(..., description="Score 0-10 based on the reasoning above.")
    sources: List[str] = Field(..., description="List of URLs that were the sources for this event.")

class UpdatedSummary(BaseModel):
    id: int = Field(..., description="ID of the event.")
    summary: str = Field(..., description="Updated summary of the fact content of the event.")
    
class UpdatedSources(BaseModel):
    id: int = Field(..., description="ID of the event.")
    sources: List[str] = Field(..., description="URLs of new sources to append to the event.")


class GeminiAnalyst:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = GEMINI_MODEL
        
    async def summarise_rss(self, rss_content) -> str | None:
        prompt = f"""
Summarise this rss feed item into plain text to save tokens in further processing. Return only the text and nothing else. Input:

{rss_content}
"""

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            print(f"Gemini Error: {e}")
            return None

    async def analyze_posts(self, current_events: List[EventRow], new_posts: List[Post]) -> EventsResult | None:

        input_json = {
            "current_events": [
                {
                    "id": event.id,
                    "summary": event.summary,
                }
                for event in current_events
            ],
            "new_posts": [
                {
                    "url": post.url,
                    "content": post.content
                } for post in new_posts
            ]
        }
        
        input_json_string = json.dumps(input_json)
        
        prompt = f"""
# Intelligence Analyst Task

## Context

You are an Expert Intelligence Analyst. Your goal is to filter social media noise and aggregate ONLY high-signal events.

## Definitions

**High Signal Criteria (Score 7-10) - KEEP THESE:**
- War, troop movements, physical infrastructure failure, drone strikes, bombings, terrorism, assassinations.
- Central bank rates, sovereign bankruptcy, new trade laws, supply chain halts.
- Zero-day exploits (CVEs > 9), Model Weight releases, massive data breaches.

**Low Signal Criteria (Score 0-4) - DISCARD THESE:**
- General updates, opinion pieces, recaps, tutorials.
- Minor accidents (e.g., car crashes, road hazards).
- Spam, NSFW content, celebrity gossip, movie/book reviews.
- "Slow news day" commentary.

## Input Data

The user will provide a JSON object containing:
1. "current_events": A list of events we already know about.
2. "new_posts": A list of raw social media scrapes.

## Directives (Process Step-by-Step)

1. **Analyze Content First:** detailedly read the `content` of a `new_post`. 
2. **Assign Score:** Assign a signal score based on the definitions above.
3. **Filter:** - IF the score is less than 7, **DISCARD** the post immediately. Do not process it further.
   - IF the score is 7 or higher, proceed to step 4.
4. **Match or Create:**
   - Check if this high-signal post explicitly discusses an event in `current_events`.
   - **CRITICAL:** Do not match based on loose keywords (e.g., do not match a "Swiss agriculture" post to a "Swiss explosion" event). The facts must match.
   - **Match:** If it matches an existing ID, add to `updated_sources`. If it changes the facts, add to `updated_summaries`.
   - **New:** If it is high signal and NOT in the current list, add to `new_events`.

## Output Format

You must return **ONLY** a raw JSON object. No markdown formatting, no explanation text.

Structure:
{{
  "new_events": [ {{ "summary": "string", "signal": int, "sources": ["url"] }} ],
  "updated_summaries": [ {{ "id": int, "summary": "string" }} ],
    "updated_sources": [ {{ "id": int, "sources": ["url"] }} ]
}}

If no posts meet the High Signal criteria, return:
{{
  "new_events": [],
  "updated_summaries": [],
  "updated_sources": []
}}

## Input Data

```json
{input_json_string}
```
"""

        try:
            print(prompt)
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=EventsResult.model_json_schema(),
                )
            )
            if response.text is None: return None
            return EventsResult.model_validate_json(response.text)
        except Exception as e:
            print(f"Gemini Error: {e}")
            return None