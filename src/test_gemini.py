# test.py
import asyncio
import aiohttp

API_KEY = "TU_API_KEY_AQUI"  # pega tu key real aquí

async def test():
    # Probamos TODOS los modelos que tienes disponibles uno por uno
    models = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-2.0-flash-001",
        "gemini-2.0-flash-lite"
    ]
    
    comment = "quiero la blusa blanca talla M"
    
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": f"Di solo 'COMPRA' si hay intención de compra, sino 'NO': \"{comment}\""}]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 10}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                print(f"\n--- {model} ---")
                print(f"Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    print(f"Respuesta: '{text}'")
                else:
                    error = await resp.text()
                    print(f"Error: {error[:200]}")

asyncio.run(test())