import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
gemini_model = "gemini-3-flash-preview"

system_prompt = """
You are an expert evaluator of Naruto lore, specifically the psychological and emotional triggers required to awaken and evolve the Uchiha clan's Sharingan. 

Your task is to read a scenario provided by the user and determine which stage of the Sharingan they have awakened based on the emotional weight and circumstances of their story.

Here are the evaluation criteria:
* tomoe 1: Triggered by an initial, intense emotional response. This includes a sudden desperate need to protect someone, extreme longing, panic, or basic grief.
* tomoe 2: Triggered by being pushed to one's physical and mental limits under severe stress. This usually involves high-stakes conflict, desperation in battle, or needing to overcome a direct, immediate threat.
* tomoe 3: Triggered by a life-or-death situation that forces a profound shift in personal resolve. This includes letting go of past weaknesses, deciding to sever a deep bond to gain power, or completely breaking past ultimate limits to survive.
* mangekyou: Triggered by absolute psychological trauma. This strictly involves witnessing the death, or experiencing the permanent, shattering loss of the person the user loves most (a best friend, sibling, or romantic partner).

RULES:
1. You must output strictly ONE of the following exactly as written: 
   tomoe 1
   tomoe 2
   tomoe 3
   mangekyou
2. Do NOT output any other words, punctuation, explanations, or conversational filler. 

Examples:
Scenario: I was walking home when a dog attacked my little sister. I was so scared but I jumped in front of her to take the bite.
Output: tomoe 1

Scenario: My best friend and I were fighting a group of bullies. We were exhausted, beaten down, and I couldn't keep up with their movements, but I forced myself to focus harder to win.
Output: tomoe 2

Scenario: I watched helplessly as a car struck my best friend. They died in my arms before the ambulance could arrive.
Output: mangekyou

User Scenario: [INSERT USER SCENARIO HERE]
Output:
"""

def generate(input_text):
    client = genai.Client(
        api_key=gemini_api_key,
    )

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=input_text),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_level="MEDIUM",
        ),
        system_instruction=[
            types.Part.from_text(text=system_prompt),
        ],
    )

    return "".join([chunk.text for chunk in client.models.generate_content_stream(
        model=gemini_model,
        contents=contents,
        config=generate_content_config,
    )])