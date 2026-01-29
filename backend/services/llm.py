from google import genai
from backend.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def ask_llm(prompt: str):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

if __name__ == "__main__": 
    print(ask_llm("Explain quantum physics to a 5-year-old."))