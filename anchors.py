from ai_engine import GeminiAnalyst
import joblib
import asyncio

HIGH_SIGNAL_ANCHORS = [
    # Kinetic / Conflict Events
    "Breaking news: Massive explosion reported in downtown area with multiple casualties.",
    "Military airstrikes confirmed against foreign targets.",
    "War declared: Government mobilizes troops to the border.",
    "Terrorist attack involving bombs and gunfire.",
    "Assassination attempt on political leader.",
    
    # Natural Disasters / Major Accidents
    "Magnitude 7.0 earthquake strikes major city, buildings collapsed.",
    "Tsunami warning issued for coastal regions following quake.",
    "Catastrophic port explosion causes widespread destruction.",
    "Hurricane makes landfall causing severe flooding and power outages.",
    
    # Political / Geopolitical Instability
    "Military coup underway: President detained by armed forces.",
    "Government announces immediate sanctions and cuts diplomatic ties.",
    "Riots break out in the capital city, police use tear gas.",
    "State of emergency declared following civil unrest.",
    
    # Generic "Urgency" Markers (Good for catching miscellaneous breaking news)
    "URGENT: Reports coming in of a major developing situation.",
    "Flash update: Confirmed fatalities in ongoing disaster.",
    "Official statement regarding the crisis situation."
]

LOW_SIGNAL_ANCHORS = [
    # Furry / Fan Art / Creative (Very distinct vocabulary)
    "Here is a sketch of my fursona I drew last night!",
    "Open for commissions! DM me for prices on digital art.",
    "Check out this cute fanart I made for my favorite character.",
    "WIP of my latest drawing, still need to do the shading.",
    "Retweeting this amazing piece of art by my friend.",
    
    # Personal / Blog / Vlogging
    "Just woke up and had the best coffee ever.",
    "My cat is being so funny today, look at him sleeping.",
    "I am so tired of work today, can't wait for the weekend.",
    "Going live on Twitch to play some Minecraft, come hang out!",
    "Update on my life: sorry I haven't been posting much lately.",
    
    # "Content" / Listicles / Clickbait (Technically "media" but usually low signal)
    "Top 10 funny moments from last year you missed.",
    "You won't believe what happened in this video game.",
    "Check out my new unboxing video on YouTube.",
    "Reaction video: My thoughts on the latest movie trailer.",
    "BREAKING NEWS",
    
    # Generic Internet Slang / Shitposting
    "LMAO this is actually so true.",
    "Just a random thought I had in the shower.",
    "Why is everyone talking about this? I don't get it."
]

async def create_anchors():
    gemini = GeminiAnalyst()

    high_anchors = [gemini.get_embedding(text) for text in HIGH_SIGNAL_ANCHORS]
    low_anchors = [gemini.get_embedding(text) for text in LOW_SIGNAL_ANCHORS]
    high_anchors = await asyncio.gather(*high_anchors)
    low_anchors = await asyncio.gather(*low_anchors)

    joblib.dump(high_anchors, "high_signal_anchors.pkl")
    joblib.dump(low_anchors, "low_signal_anchors.pkl")

if __name__ == "__main__":
    asyncio.run(create_anchors())