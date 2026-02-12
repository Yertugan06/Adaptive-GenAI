from google import genai
from backend.core.config import settings
from transformers import AutoTokenizer

client = genai.Client(api_key=settings.GEMINI_API_KEY)
DEFAULT_MODEL = "gemini-2.5-flash"
TOKENIZER = AutoTokenizer.from_pretrained("backend/ml_models/multilingual-e5-base")


async def ask_llm(prompt: str) -> str:
    response = client.models.generate_content(
        model=DEFAULT_MODEL,
        contents=prompt
    )
    return response.text #type: ignore


async def summarize(text :str) -> str:
    prompt = (
        f"INSTRUCTION: Summarize the text below. Focus only on core semantic facts. "
        f"No introductory phrases. Maximum output length is 450 tokens.\n\n"
        f"CONTENT TO SUMMARIZE:\n{text}"
    )
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=prompt,
        config={
            "temperature": 0.1, 
            "max_output_tokens": 470
        }
    )
    return response.text.strip() #type: ignore

if __name__ == "__main__": 
    print(ask_llm("Explain quantum physics to a 5-year-old."))