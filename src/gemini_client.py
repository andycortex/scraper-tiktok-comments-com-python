import re
import json
import aiohttp
from config import Config

API_URL = f"https://generativelanguage.googleapis.com/v1/models/{Config.MODEL}:generateContent?key={Config.GEMINI_API_KEY}"

def build_prompt(comment: str) -> str:
    labels = "',\n    '".join(Config.CANDIDATE_LABELS)
    return (
        f"Clasifica este comentario EXACTAMENTE en una de las siguientes categorías:\n"
        f"    '{labels}'\n\n"
        f"Responde SOLO con un objeto JSON con la clave \"clasificacion\" y la etiqueta completa.\n"
        f"Sin explicaciones, sin markdown, sin saltos extra.\n\n"
        f"Comentario: \"{comment}\""
    )

def build_payload(comment: str) -> dict:
    return {
        "contents": [{"parts": [{"text": build_prompt(comment)}]}],
        "generationConfig": {
            "temperature": 0.1,
            "topP": 0.95,
            "maxOutputTokens": 100
        }
    }

def extract_json(text: str) -> str:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No se encontró JSON válido")
    return match.group(0)

def find_best_label(returned: str) -> str:
    returned = returned.strip().lower()
    for label in Config.CANDIDATE_LABELS:
        if returned in label.lower() or label.lower().startswith(returned):
            return label
    return Config.CANDIDATE_LABELS[-1]  # fallback: neutral

async def classify_comment(session: aiohttp.ClientSession, comment_text: str) -> str:
    payload = build_payload(comment_text)
    async with session.post(API_URL, json=payload, timeout=30) as resp:
        if resp.status != 200:
            error = await resp.text()
            raise Exception(f"Gemini error {resp.status}: {error}")
        data = await resp.json()

    raw = data.get("candidates", [{}])[0] \
              .get("content", {}) \
              .get("parts", [{}])[0] \
              .get("text", "")

    if not raw:
        raise Exception("Respuesta vacía de Gemini")

    json_str = extract_json(raw)
    result = json.loads(json_str)
    clasificacion = result.get("clasificacion", "").strip()

    return find_best_label(clasificacion)