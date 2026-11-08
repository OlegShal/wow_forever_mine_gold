# Точка входа Python-функции Vercel: все /api/* переписываются сюда (vercel.json).
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api import app  # noqa: E402,F401
