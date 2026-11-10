# Kirana Voice Ledger - voice-first accounting for small shopkeepers

A voice-first ledger application designed for Indian kirana store owners to record daily grocery transactions hands-free using speech recognition and synthesis.

Built for the Great Indian AI Internship Challenge by Gnani.ai.

## Problem
Small shopkeepers in India typically keep accounts on paper notebooks or skip them altogether during busy hours because modern digital bookkeeping applications require typing in English, which presents a language and usability barrier.

## Solution & How It Works
Kirana Voice Ledger allows the shopkeeper to speak naturally in Hindi, Hinglish, or Gujarati.
1. The shopkeeper speaks the transaction details.
2. Gnani Prisma (speech-to-text) transcribes the speech.
3. The application parser extracts items and the transaction total, supporting Hindi number words (e.g. "ek sau bees" = 120) in both Latin and Devanagari scripts.
4. The entry is recorded into a running `ledger.json` file.
5. Gnani Timbre v2.5 (text-to-speech) synthesizes and reads the total and running balance back in Hindi.

### Flow Diagram
```text
Voice -> Prisma STT -> Parser -> Ledger -> Timbre TTS -> Voice reply
```

## Models Used
- Gnani Prisma (speech-to-text, default account model: [PRISMA_MODEL_NAME])
- Gnani Timbre v2.5 (text-to-speech, voice Kaveri)
- Evon is not used in this project.

## Users
- Kirana shop owners
- Small retail businesses

## Setup

### 1. Install Dependencies
Ensure Python is installed, then install requirements:
```bash
pip install -r requirements.txt
```

### 2. Set API Key
Set your Gnani API key in your terminal environment. Never commit your key to version control or share it publicly.

**Windows PowerShell:**
```powershell
$env:GNANI_API_KEY = "<your key>"
```

**Linux / macOS (Bash):**
```bash
export GNANI_API_KEY="<your key>"
```

## Usage

### 1. Record a Voice Note
Record audio from your microphone:
```bash
python record_wav.py
```

### 2. Process Voice Note in Ledger
Run `app.py` with the recorded `.wav` file:
```bash
python app.py --wav test.wav
```

For Gujarati voice notes, specify the language code:
```bash
python app.py --wav test.wav --lang gu-IN
```

### Example
**Voice input:**
```text
"do kilo chawal, ek packet namak, kul ek sau bees rupaye"
```

**Application output:**
```text
Items: ['chawal', 'namak']
Total this entry: Rs 120
Ledger: 1 entries, running total Rs 120 (saved to ledger.json)
Timbre read-back saved to total_reply.wav: Kul 120 rupaye. Aaj ka kul 120 rupaye. Dhanyavaad.
```

## Project Structure
```text
kirana-voice-ledger/
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── app.py
└── record_wav.py
```

## Limitations
- Word mapping: "tees" maps to 30.
- Gujarati number words are not parsed (requires numeric digits or Hindi words).
- Single language code per request due to SDK limitations.
- The item catalog is based on a fixed word list.
- Command-line interface only.

## Data and Privacy
This project uses synthetic data only. Audio was recorded using the author's own voice. No real customer audio or personal data is collected or stored.

## Built By
Dhruv, CS student at SVNIT Surat - solo project, did all the work (idea, code, testing, demo).

#GreatIndianAIInternshipChallenge #GnaniAI
