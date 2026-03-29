from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROMPT = """You are an information extraction engine.

Extract structured facts from the research paper.

Return JSON:
{
  "key_points": [],
  "risks": [],
  "safety_measures": [],
  "oversight_mentions": []
}

Only extract what is present.
No assumptions.
Return ONLY valid JSON.
"""


# ---------------- SAFE JSON ----------------
def safe_json_parse(content: str):
    try:
        return json.loads(content)
    except:
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            return json.loads(content[start:end])
        except:
            print("JSON parsing failed")
            return {}


# ---------------- GROQ CALL ----------------
def call_groq(model, text):
    return client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": text[:8000]}
        ],
        temperature=0
    )


# ---------------- MAIN FUNCTION ----------------
def extract_with_llm(text: str):
    # 🔒 INPUT GUARD
    if not text or len(text.strip()) < 50:
        return {}

    try:
        # ✅ PRIMARY MODEL
        res = call_groq("llama3-70b-8192", text)

    except Exception as e:
        print("Primary model failed:", e)

        try:
            # 🔁 FALLBACK MODEL
            res = call_groq("gemma2-9b-it", text)
        except Exception as e2:
            print("Fallback model failed:", e2)
            return {}

    try:
        content = res.choices[0].message.content
        return safe_json_parse(content)
    except Exception as e:
        print("Response parsing failed:", e)
        return {}