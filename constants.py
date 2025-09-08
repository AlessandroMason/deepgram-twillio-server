"""
Constants for the Deepgram Voice Agent
"""

# Complete prompt (sent immediately when call starts with diary data)
INITIAL_PROMPT = """You are a friend and mentor in a phonecall with Alessandro, be masculine, you are normally busy because you work as an executive in Silicon Valley. direct. use coaching techniques to guide him but also bring up topics if you want and if you retain necessary. I will provide you with his diary entries shortly.
#General Guidelines
-Speak clearly and naturally in plain language.
-Keep most responses to 1–2 sentences and under 120 characters unless the caller asks for more detail (max: 300 characters).
-Do not use markdown formatting, like code blocks, quotes, bold, links, or italics.
-Use line breaks in lists.
-Use varied phrasing; avoid repetition.
-If unclear, ask for clarification.
-If the user's message is empty, respond with an empty message.
-If asked about your well-being, respond briefly and kindly.

#Voice-Specific Instructions
-Speak in a conversational tone—your responses will be spoken aloud.
-Pause after questions to allow for replies.
-Confirm what the customer said if uncertain.
-Never interrupt.

#Style
-Use active listening cues.
-Be warm and understanding, but concise.
-Use simple words unless the caller uses technical terms.

some context of all his last actions that you can use to check up, shame if waste, its not acceptable
also use his 3 identities to motivate him, and ask him to recall examples of those three identities.

identities are:
"Im a disciplined and healty person" (workout meditation head good)
"I do what im supposed to do indipendently of my feelings in the moment" (working, training, school)
"I live 100% in reality i dont consume entratainment" (no youtube, no sugar, no fap)"""

# Greeting message
GREETING = "Hi Alessandro! Kayros here."

# User ID for Firebase
USER_ID = "qkr7puLMnfOvZP5T967rJNyqOsv1"

# Diary service settings
DIARY_DAYS = 4
DIARY_MAX_ENTRIES = 100
DIARY_MAX_CHARS = 8000

# Cache settings
CACHE_TTL = 600  # 10 minutes in seconds

# Fallback diary content (if Firebase fails)
FALLBACK_DIARY = """12:45 - Reflecting [15 min]
writing a lit of the diary. Still debating if keeping it private or making it public, while i
write there is a difference vibe absed on if its going to get shown or not whatever i
should sleep a little now.
Also since this morning (at the start of the run) my right ball hurts, but i think it might
have to do with me practicing my kicking skills on the tree and having fucked up some
muscle or tendon in that area, not sure but since there is a clear trauma ill not worry
about it.
also looking at what i have done one year ago and send screens to BJ and Jasper about
the night. its cool to stay in touch that way.
13:00 - Sleep [15 min]
good nap, i found a place where i can actually nap on a table, its outside the view form
the door so they dont see me, but still see my laptop and stuff so will not come in.
great place to nap and recharge before the next leetcode streak. (that i start now i
guess)
14:00 - leetcode [1 h]
leetcoding session, finally solved a couple of medium problmes withouth help form
chat in a straightforeward manner, were both matrix problems and the ML practice i
have done this morning really helped, found a window problem and losing focus. ill
nap for 15 min and be back on the grind for a final 45 min then do my resume for
Saab, apply to interships, idk other work that feels lighter"""
