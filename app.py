"""
Gnani.ai - kirana voice ledger (corrected version).
Challenge: Great Indian AI Internship Challenge, submit by Tue 2026-11-10, 11:59 PM IST.
Models: Prisma v2.5 (STT) + Timbre v2.5 (TTS).

Setup (PowerShell):
    pip install gnani-vachana
    $env:GNANI_API_KEY = "<your key>"

Run:
    python app.py --wav test.wav
    python app.py --wav test.wav --lang gu-IN   # Gujarati

Changes from the original:
  - Removed "so": 100 (common English filler in Hinglish, caused wrong totals).
  - Total now prefers the number spoken right after "kul"/"total"/"jama",
    and falls back to the largest figure.
  - UTF-8 console output (Windows PowerShell can crash on Hindi text).
  - Prints the raw STT result so the transcript key can be checked.
  - Handles TTS result being bytes or a non-bytes object without crashing.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from gnani.stt import GnaniSTTClient
from gnani.tts import GnaniTTSClient, AudioConfig

LEDGER = "ledger.json"
REPLY_WAV = "total_reply.wav"

ITEM_WORDS = ["chawal", "rice", "namak", "salt", "atta", "tel", "oil",
              "chini", "sugar", "dal", "doodh", "milk", "sabzi", "sabji",
              "besan", "masala", "chai", "biscuit"]

# Devanagari spellings Prisma may return for hi-IN -> canonical item word.
DEVANAGARI_ITEMS = {
    "चावल": "chawal", "नमक": "namak", "आटा": "atta", "तेल": "tel",
    "चीनी": "chini", "दाल": "dal", "दूध": "doodh", "सब्जी": "sabzi",
    "सब्ज़ी": "sabzi", "बेसन": "besan", "मसाला": "masala", "चाय": "chai",
    "बिस्किट": "biscuit", "बिस्कुट": "biscuit",
}

# "tees" = 30 (23 is ambiguous and rare in a shop total).
HINDI_NUMBERS = {
    "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5, "panch": 5,
    "chhe": 6, "chhah": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
    "gyarah": 11, "barah": 12, "terah": 13, "chaudah": 14, "pandrah": 15,
    "solah": 16, "satrah": 17, "atharah": 18, "unnis": 19,
    "bees": 20, "tees": 30, "chalis": 40, "pachas": 50, "saath": 60,
    "sattar": 70, "assi": 80, "nabbe": 90,
    "sau": 100, "hazar": 1000, "hajar": 1000,
    # Devanagari
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6,
    "छः": 6, "छे": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
    "ग्यारह": 11, "बारह": 12, "तेरह": 13, "चौदह": 14, "पंद्रह": 15,
    "पन्द्रह": 15, "सोलह": 16, "सत्रह": 17, "अठारह": 18, "उन्नीस": 19,
    "बीस": 20, "तीस": 30, "चालीस": 40, "पचास": 50, "साठ": 60,
    "सत्तर": 70, "अस्सी": 80, "नब्बे": 90,
    "सौ": 100, "हज़ार": 1000, "हजार": 1000,
}

TOTAL_KEYWORDS = {"kul", "total", "jama", "कुल", "टोटल", "जमा"}


def _hindi_number_value(words: list[str]) -> int:
    """Convert a run of Hindi number words to an int, e.g. ek sau bees -> 120."""
    total, current = 0, 0
    for w in words:
        v = HINDI_NUMBERS[w]
        if v == 1000:
            total += (current or 1) * 1000
            current = 0
        elif v == 100:
            current = (current or 1) * 100
        else:
            current += v
    return total + current


def parse_ledger(transcript: str) -> tuple[list[str], int | None]:
    """Pull item words and the total out of a transcript (Latin or Devanagari)."""
    lowered = re.sub(r"(?<=\d),(?=\d)", "", transcript.lower())  # 1,200 -> 1200
    tokens = [t for t in re.split(r"[\s,.;:!?|।\"'()\-]+", lowered) if t]

    items: list[str] = []
    for t in tokens:
        name = DEVANAGARI_ITEMS.get(t, t)
        if name in ITEM_WORDS and name not in items:
            items.append(name)

    amounts: list[tuple[int, int]] = []  # (token_index, value)
    run: list[str] = []
    run_start = 0
    for i, tok in enumerate(tokens + [""]):
        if tok in HINDI_NUMBERS:
            if not run:
                run_start = i
            run.append(tok)
        else:
            if run:
                amounts.append((run_start, _hindi_number_value(run)))
                run = []
            if tok and tok.isdigit():  # ASCII or Devanagari digits
                amounts.append((i, int(tok)))

    if not amounts:
        return items, None
    for idx, val in amounts:  # prefer the number right after "kul"/"total"
        if idx > 0 and tokens[idx - 1] in TOTAL_KEYWORDS:
            return items, val
    return items, max(v for _, v in amounts)


def load_ledger() -> list[dict]:
    if not os.path.exists(LEDGER):
        return []
    with open(LEDGER, encoding="utf-8") as f:
        return json.load(f)


def save_ledger(entries: list[dict]) -> None:
    with open(LEDGER, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def main() -> int:
    ap = argparse.ArgumentParser(description="Kirana voice ledger (Gnani Prisma + Timbre)")
    ap.add_argument("--wav", required=True, help="voice note, e.g. test.wav")
    ap.add_argument("--lang", default="hi-IN",
                    help="ONE language code (SDK rejects combined codes): hi-IN, en-IN, gu-IN, ...")
    ap.add_argument("--voice", default="Kaveri",
                    help="Timbre voice for the read-back (documented timbre-v2.5 voice)")
    args = ap.parse_args()

    if not os.environ.get("GNANI_API_KEY"):
        print('Set GNANI_API_KEY first (PowerShell): $env:GNANI_API_KEY = "<your key>"')
        return 1
    if not os.path.exists(args.wav):
        print(f"Missing {args.wav} - record a ~10s Hinglish voice note (python record_wav.py).")
        return 1

    stt = GnaniSTTClient()  # picks up GNANI_API_KEY
    result = stt.transcribe(args.wav, language_code=args.lang)
    print("RAW:", result)  # remove once the transcript key is confirmed
    if isinstance(result, dict):
        transcript = (result.get("transcript") or result.get("text")
                      or result.get("transcription") or "")
    else:
        transcript = str(result)
    print("Transcript:", transcript)
    if isinstance(result, dict):
        print("STT model reported by API:", result.get("model"))

    items, total = parse_ledger(transcript)
    print("Items:", items or "(none matched - extend ITEM_WORDS)")
    print("Total this entry:", f"Rs {total}" if total is not None else "(no amount heard)")
    if total is None:
        print("No amount heard - re-record with the total spoken clearly, "
              "e.g. 'kul ek sau bees rupaye'.")
        return 0

    entries = load_ledger()
    entries.append({
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "wav": args.wav, "lang": args.lang,
        "transcript": transcript, "items": items, "total_rs": total,
    })
    save_ledger(entries)
    running = sum(e["total_rs"] for e in entries)
    print(f"Ledger: {len(entries)} entries, running total Rs {running} (saved to {LEDGER})")

    reply = f"Kul {total} rupaye. Aaj ka kul {running} rupaye. Dhanyavaad."
    tts = GnaniTTSClient()
    audio = tts.synthesize(
        reply, voice=args.voice,
        model="timbre-v2.5", language="hi-IN",
        audio_config=AudioConfig(sample_rate=44100, encoding="linear_pcm", container="wav"),
    )
    if isinstance(audio, (bytes, bytearray)):
        with open(REPLY_WAV, "wb") as f:
            f.write(audio)
        print(f"Timbre read-back saved to {REPLY_WAV}: {reply}")
    else:
        print("TTS returned a non-bytes object; inspect it:", type(audio), audio)
        return 1
    print(f"Demo line: shopkeeper spoke Hinglish, Prisma heard '{transcript}', "
          f"ledger total Rs {total}, Timbre read it back.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
