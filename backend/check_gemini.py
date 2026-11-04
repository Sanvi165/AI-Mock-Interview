"""Helper: checks every AI key in backend/.env.   Run from the backend folder:  python check_gemini.py"""
import sys
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env", override=True)
sys.path.insert(0, str(HERE))

from app.services import ai_service  # noqa: E402

names = ai_service._provider_order()
if not names:
    raise SystemExit(
        "No AI key found. Check that backend/.env exists, is saved, and has at least one line "
        "such as GEMINI_API_KEY=... or GROQ_API_KEY=..."
    )

print("AI services that will be tried, in this order:", ", ".join(names))
working = 0
for name in names:
    try:
        reply = ai_service._ask_provider(name, 'Reply with only this JSON: {"ok": true}')
        print(f"[OK]     {name}: {reply[:60]!r}")
        working += 1
    except ai_service.AIServiceError as exc:
        print(f"[FAILED] {name}: {exc}")
print(f"\n{working} of {len(names)} services work.")