from google import genai
from google.genai.types import GenerateContentConfig, EmbedContentConfig
from pydantic import BaseModel, Field
from domain.post import Post
from datetime import datetime
from typing import List
import re
import json
import numpy as np
from numpy import float64
from numpy.typing import NDArray
from db import EventRow
from env import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_EMBEDDING_MODEL, GEMINI_EMBEDDING_LENGTH



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

class SummarisePost(BaseModel):
    summary: str = Field(..., description="Concise summary of the fact content of the event.")
    signal: int = Field(..., description="Score 0-10 based on the reasoning above.")


class GeminiAnalyst:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = GEMINI_MODEL

    async def get_embedding(self, post: Post) -> NDArray[float64] | None:
        clean_post_content = self._clean_for_embedding(post.content)

        payload = f"Post by author {post.author_id} with content: {clean_post_content}"

        try:
            response = await self.client.aio.models.embed_content(
                model=GEMINI_EMBEDDING_MODEL,
                contents=payload,
                config=EmbedContentConfig(
                    output_dimensionality=GEMINI_EMBEDDING_LENGTH,
                    task_type="CLASSIFICATION"
                )
            )
            if response.embeddings is None: return None
            embedding_values_np = np.array(response.embeddings[0].values)
            normed_embedding = embedding_values_np / np.linalg.norm(embedding_values_np)
            return normed_embedding
        except Exception as e:
            print(f"Gemini Error: {e}")
            return None


    def _clean_for_embedding(self, text: str) -> str:
        text = text.replace("\n", " ")
        # 1. STRIP MARKDOWN LINKS: [Text](url) -> Text
        # Captures the text inside [], ignores the () part
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # 2. STRIP IMAGES: ![Alt](url) -> "" (Or keep alt text if you prefer)
        text = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', text)

        # 3. NUKE RAW URLS: https://... -> ""
        # URLs confuse semantic models.
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

        # 4. FIX HASHTAGS: #WarInVenezuela -> War In Venezuela
        def split_hashtag(match):
            tag = match.group(0)[1:] # Remove #
            # Split CamelCase: "WarInVenezuela" -> "War In Venezuela"
            return " " + " ".join(re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', tag))
        
        text = re.sub(r'#[A-Za-z0-9_]+', split_hashtag, text)

        # 5. CLEAN WHITESPACE
        text = re.sub(r'\s+', ' ', text).strip()

        return text

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
        

    async def summarise_post(self, post_content: str) -> SummarisePost | None:

        prompt = f"""
# Intelligence Analyst Task

## Context
You are an Expert Intelligence Analyst. Your goal is to filter social media noise and aggregate ONLY high-signal events into standardized, vector-friendly summaries.

## Definitions
**High Signal Criteria (Score 7-10) - KEEP THESE:**
- **Geopolitical acts:** War, troop movements, drone strikes, bombings, confirmed terrorism, assassinations.
- **Economic/Cyber:** Central bank rates, sovereign bankruptcy, new trade laws, supply chain halts, Zero-day exploits (CVEs > 9), Model Weight releases, massive data breaches.
- **Critical Infrastructure:** Total physical infrastructure failure (e.g., grid collapse, dam failure) affecting a large region.

**Low Signal Criteria (Score 0-4) - DISCARD THESE:**
- General updates, opinion pieces, recaps, tutorials.
- **Civilian Accidents & Disasters:** Plane crashes, train derailments, fires, or natural disasters **UNLESS** there is immediate confirmation of terrorism, an act of war, or it involves a Head of State.
- Spam, NSFW content, celebrity gossip, movie/book reviews.
- "Slow news day" commentary.
- Singular domestic events (local crime, protests without national impact).

## Directives (Process Step-by-Step)
1. **Analyze Content:** Detailedly read the content.
2. **Assign Score:** Assign a signal score based on the definitions above.
3. **Filter:** IF the score is less than 6, **DISCARD** the post immediately. Return an empty string summary and signal 0.
4. **Standardize & Summarize:** IF the score is more than 6, create a summary optimized for vector clustering:
   - **Entity Normalization:** Use the most specific, universally recognized name for entities.
   - **Syntax:** strict **[Subject] [Action] [Object]** format.
   - **Tone:** Clinical and dry. Remove all adjectives (e.g., "shocking", "massive") unless defining the scale (e.g., "7.8 magnitude").
   - *Example:* "Trump suggests buying Greenland." (Not: "The US President has discussed the idea of purchasing Greenland.")
5. **RETHINK SIGNAL:** Rescore based on the boring summary. If it no longer seems critical, discard.

## Output Format

You must return **ONLY** a raw JSON object. No markdown formatting, no explanation text.

Structure:
{{ "summary": "string", "signal": int }} ],

If no posts meet the High Signal criteria, return:
{{ "summary": "", "signal": 0 }}

## Input Data

```md
{post_content}
```
"""

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=SummarisePost.model_json_schema(),
                )
            )
            if response.text is None: return None
            return SummarisePost.model_validate_json(response.text)
        except Exception as e:
            print(f"Gemini Error: {e}")
            return None