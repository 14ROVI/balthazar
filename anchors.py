from ai_engine import GeminiAnalyst
import joblib
import asyncio

BUY_ANCHORS = [
    # Inflation / Economic Weakness (Positive for Silver)
    "CPI data comes in hotter than expected, inflation fears spooking markets.",
    "US GDP growth revised downwards, raising concerns of a potential recession.",
    "Federal Reserve hints at pausing rate hikes amid weakening economic outlook.",
    "Weekly jobless claims unexpectedly jump, signaling a cooling labor market.",

    # Geopolitical Instability (Positive for Silver)
    "Geopolitical tensions flare up in the Middle East, traders rush to safe-haven assets.",
    "Military exercises reported near contested border, escalating regional conflict.",
    "New sanctions announced against major global oil producer.",

    # Pro-Silver Demand/Supply News
    "Major industrial report shows silver demand for solar panels has doubled year-over-year.",
    "Investors are increasingly buying physical silver and gold as a hedge against market volatility.",
    "Major silver mine in Peru announces indefinite production halt due to labor strikes."
]

SELL_ANCHORS = [
    # Strong Economy / "Risk-On" (Negative for Silver)
    "Strong jobs report shows the economy is resilient, bolstering the US Dollar.",
    "Global stock markets rally as geopolitical tensions ease and corporate earnings beat expectations.",
    "US Dollar Index (DXY) hits a new multi-year high, putting pressure on commodity prices.",

    # Hawkish Central Bank Policy (Negative for Silver)
    "Federal Reserve Chair reiterates commitment to fighting inflation with aggressive rate hikes.",
    "European Central Bank signals a more hawkish stance, preparing for rate increases.",

    # Anti-Silver Demand/Supply News
    "Breakthrough in manufacturing reduces the amount of silver needed in electronic components.",
    "Large new silver deposit discovered in Mexico, expected to significantly increase global supply.",
    "Scrap silver recycling hits an all-time high, flooding the market with new supply."
]

NOISE_ANCHORS = [
    # Personal / Blog / Vlogging
    "Just woke up and had the best coffee ever.",
    "My cat is being so funny today, look at him sleeping.",
    "Going live on Twitch to play some Minecraft, come hang out!",
    "Update on my life: sorry I haven't been posting much lately.",

    # Art / Creative / Spam
    "Here is a sketch of my fursona I drew last night!",
    "Open for commissions! DM me for prices on digital art.",
    "You won't believe what happened in this video game.",
    "Check out my new unboxing video on YouTube.",
    
    # Generic Internet Slang / Miscellaneous
    "LMAO this is actually so true.",
    "Why is everyone talking about this? I don't get it.",
    "Happy Friday everyone!",
    "Does anyone have a good recipe for banana bread?"
]

async def create_anchors():
    gemini = GeminiAnalyst()

    buy_embeddings = [gemini.get_embedding(text) for text in BUY_ANCHORS]
    sell_embeddings = [gemini.get_embedding(text) for text in SELL_ANCHORS]
    noise_embeddings = [gemini.get_embedding(text) for text in NOISE_ANCHORS]
    
    buy_embeddings = await asyncio.gather(*buy_embeddings)
    sell_embeddings = await asyncio.gather(*sell_embeddings)
    noise_embeddings = await asyncio.gather(*noise_embeddings)

    joblib.dump(buy_embeddings, "buy_anchors.pkl")
    joblib.dump(sell_embeddings, "sell_anchors.pkl")
    joblib.dump(noise_embeddings, "noise_anchors.pkl")


if __name__ == "__main__":
    asyncio.run(create_anchors())