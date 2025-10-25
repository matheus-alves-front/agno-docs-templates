from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    TEMPLATES: str = os.path.join(ROOT, "templates")
    SPECS: str = os.path.join(ROOT, "specs")
    RESULTS: str = os.path.join(ROOT, "results")

    OLLAMA_HOST: str | None = os.getenv("OLLAMA_HOST") or None
    OLLAMA_MODEL: str | None = os.getenv("OLLAMA_MODEL") or None

settings = Settings()
for d in (settings.TEMPLATES, settings.SPECS, settings.RESULTS):
    os.makedirs(d, exist_ok=True)
