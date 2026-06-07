import asyncio
import instructor
import google.generativeai as genai
from pydantic import BaseModel
import os

genai.configure(api_key=os.environ.get("OPENAI_API_KEY"))

class TestSchema(BaseModel):
    summary: str
    action_items: list[str]

client = instructor.from_gemini(
    client=genai.GenerativeModel(model_name="models/gemini-1.5-flash"),
    mode=instructor.Mode.GEMINI_JSON,
)

async def test():
    try:
        resp = client.chat.completions.create(
            messages=[{"role": "user", "content": "I need to fix the UI and add a database."}],
            response_model=TestSchema,
        )
        print(resp)
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
