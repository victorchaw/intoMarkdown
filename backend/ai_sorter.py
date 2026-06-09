import json
import os
import re

from openai import OpenAI

MODEL = "deepseek/deepseek-chat:free"

SYSTEM_PROMPT = """You organize books that have been split into PDF chapter files.
Given a list of PDF filenames and the book folder name, return JSON with this exact structure:
{
  "output_name": "snake_case_book_name",
  "ordered_files": ["filename1.pdf", "filename2.pdf"],
  "skipped_files": [
    {"filename": "file.pdf", "reason": "full_book_duplicate"},
    {"filename": "file2.pdf", "reason": "marketing_noise"}
  ]
}

Rules:
- ordered_files: filenames in correct reading order (Preface/Introduction first, Parts before their Chapters, Appendix/Index/References last)
- Skip files whose name closely matches the book folder name (full-book duplicate)
- Skip marketing/publisher files (e.g. "Why subscribe", "About the publisher", "Copyright")
- output_name: snake_case, concise, no publisher suffix, no special characters
- Return ONLY valid JSON. No explanation, no markdown fences."""


def _slugify(name: str) -> str:
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name.lower()


def _fallback_sort(filenames: list[str], folder_name: str) -> dict:
    return {
        "output_name": _slugify(folder_name),
        "ordered_files": sorted(filenames),
        "skipped_files": [],
    }


def sort_and_name(filenames: list[str], folder_name: str) -> dict:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key or api_key == "your_key_here":
        print("[AI] No API key — using alphabetical fallback")
        return _fallback_sort(filenames, folder_name)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    user_message = (
        f'Book folder name: "{folder_name}"\n\n'
        f"PDF files:\n" + "\n".join(f"- {f}" for f in filenames)
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
            max_tokens=2000,
        )
        raw = response.choices[0].message.content or ""
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        result = json.loads(raw)
        # validate required keys
        assert "output_name" in result
        assert "ordered_files" in result
        assert isinstance(result["ordered_files"], list)
        if "skipped_files" not in result:
            result["skipped_files"] = []
        return result
    except Exception as e:
        print(f"[AI] Sort failed ({e}) — using alphabetical fallback")
        return _fallback_sort(filenames, folder_name)
