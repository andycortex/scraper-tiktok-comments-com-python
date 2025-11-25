# src/gemini_client.py → ahora es OpenAI (pero el worker no se entera)
import aiohttp
from config import Config

# Usamos la misma variable del .env para no tocar nada más
OPENAI_API_KEY = Config.GEMINI_API_KEY  # ← reutilizamos la variable que ya tenías

async def classify_comment(session: aiohttp.ClientSession, comment_text: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Prompt ultra efectivo y barato (funciona perfecto con gpt-4o-mini y gpt-3.5-turbo)
    prompt = f"""Clasifica este comentario de TikTok Live en UNA SOLA de las siguientes categorías exactas:

• intención de compra (ej: lo quiero, dónde compro, me interesa)
• pregunta sobre precio (ej: cuánto cuesta, tiene valor)
• pregunta general (ej: dudas, consultas, información)
• elogio (ej: me gusta, buen producto, recomendación)
• queja (ej: problema, mala experiencia, no funciona)
• comentario neutral o irrelevante (ej: ok, gracias, emojis, saludos)

Comentario: "{comment_text}"

Responde SOLO con la categoría completa tal cual está arriba. Nada más."""

    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 30
    }

    try:
        async with session.post(url, headers=headers, json=payload, timeout=20) as resp:
            if resp.status == 401:
                raise Exception("OpenAI: API key inválida o sin fondos")
            if resp.status == 429:
                raise Exception("OpenAI: Rate limit alcanzado")
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"OpenAI error {resp.status}: {error_text}")

            data = await resp.json()
            result = data["choices"][0]["message"]["content"].strip()

            # Limpieza por si acaso mete comillas o puntos
            result = result.strip('."\'').strip()

            # Mapeo exacto para que coincida con tus etiquetas actuales
            mapping = {
                "intención de compra": "intención de compra (ej: lo quiero, dónde compro, me interesa)",
                "pregunta sobre precio": "pregunta sobre precio (ej: cuánto cuesta, tiene valor)",
                "pregunta general": "pregunta general (ej: dudas, consultas, información)",
                "elogio": "elogio (ej: me gusta, buen producto, recomendación)",
                "queja": "queja (ej: problema, mala experiencia, no funciona)",
            }

            for corto, largo in mapping.items():
                if corto.lower() in result.lower():
                    return largo

            # Si no reconoce nada → neutral
            return "comentario neutral o irrelevante (ej: ok, gracias, emojis, saludos)"

    except Exception as e:
        print(f"OpenAI ERROR → {e}")
        # Nunca para el worker por un solo fallo
        return "ERROR"