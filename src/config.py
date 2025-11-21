import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MODEL = "gemini-1.5-flash"

    # MySQL
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB")
    MYSQL_CHARSET = "utf8mb4"

    # Worker
    BATCH_SIZE = 5
    INTERVAL_SECONDS = 60

    # Etiquetas de clasificación
    CANDIDATE_LABELS = [
        "intención de compra (ej: lo quiero, dónde compro, me interesa)",
        "pregunta sobre precio (ej: cuánto cuesta, tiene valor)",
        "pregunta general (ej: dudas, consultas, información)",
        "elogio (ej: me gusta, buen producto, recomendación)",
        "queja (ej: problema, mala experiencia, no funciona)",
        "comentario neutral o irrelevante (ej: ok, gracias, emojis, saludos)"
    ]

# Validación rápida al importar
if not Config.GEMINI_API_KEY:
    raise ValueError("Falta GEMINI_API_KEY en el archivo .env")
if not all([Config.MYSQL_USER, Config.MYSQL_DB]):
    raise ValueError("Faltan variables de MySQL en .env")