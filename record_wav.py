"""
Record test.wav from your microphone (16 kHz, mono, 16-bit, 10 seconds).
Setup:  pip install sounddevice
Run:    python record_wav.py            (or: python record_wav.py out.wav 12)
Say:    "do kilo chawal, ek packet namak, kul ek sau bees rupaye"
Use your OWN voice only (challenge rule).
"""
import sys
import wave

import sounddevice as sd

out = sys.argv[1] if len(sys.argv) > 1 else "test2.wav"
secs = int(sys.argv[2]) if len(sys.argv) > 2 else 10
rate = 16000

print(f"Recording {secs}s... speak now!")
data = sd.rec(int(secs * rate), samplerate=rate, channels=1, dtype="int16")
sd.wait()

with wave.open(out, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(rate)
    w.writeframes(data.tobytes())
print(f"Saved {out}")
