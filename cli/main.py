"""
Command Line Interface (CLI) for AadhaarVoice.
Provides terminal access to:
- Generating and validating Verhoeff demo VIDs
- Audio feature extraction and biometric template generation
- Forensic deepfake and synthetic voice detection
- Voice synthesis and formant cloning
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure app is in python path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.verhoeff import (
    generate_demo_aadhaar,
    validate_verhoeff,
    format_aadhaar,
)
from app.ml.audio_processor import preprocess_audio, write_wav_bytes
from app.ml.feature_extractor import extract_all_features
from app.ml.deepfake_detector import detect_deepfake
from app.ml.voice_biometrics import generate_voice_embedding
from app.ml.voice_cloner import clone_speaker_voice


def cmd_generate_vid(args):
    prefix = args.prefix
    vid = generate_demo_aadhaar(prefix=prefix)
    print("\n🇮🇳 AadhaarVoice - Synthetic VID Generator")
    print("=" * 45)
    print(f"Raw Demo VID   : {vid}")
    print(f"Formatted VID : {format_aadhaar(vid, mask=False)}")
    print(f"Masked VID    : {format_aadhaar(vid, mask=True)}")
    print(f"Verhoeff Valid: {validate_verhoeff(vid)}")
    print("Disclaimer    : Educational demo identifier. Not real citizen UIDAI data.\n")


def cmd_validate_vid(args):
    vid = args.vid
    cleaned = "".join(filter(str.isdigit, vid))
    is_valid = validate_verhoeff(cleaned) if len(cleaned) == 12 else False
    print("\n🔍 Verhoeff Checksum Validation")
    print("=" * 45)
    print(f"Input VID     : {vid}")
    print(f"Cleaned Digits: {cleaned}")
    print(f"Length        : {len(cleaned)} (Required: 12)")
    print(f"Valid Checksum: {'✅ PASSED' if is_valid else '❌ FAILED'}\n")


def cmd_analyze_audio(args):
    path = Path(args.file)
    if not path.exists():
        print(f"Error: File {path} does not exist.")
        sys.exit(1)

    with open(path, "rb") as f:
        audio_bytes = f.read()

    signal, sr = preprocess_audio(audio_bytes)
    feats = extract_all_features(signal, sr)
    embedding = generate_voice_embedding(signal, sr)

    print(f"\n📊 Acoustic Biometric Analysis: {path.name}")
    print("=" * 55)
    print(f"Duration            : {feats['duration_seconds']} seconds")
    print(f"Sample Rate         : {sr} Hz")
    print(f"Fundamental Pitch F0: {feats['pitch_f0_hz']} Hz")
    print(f"Pitch Jitter        : {feats['pitch_jitter']}")
    print(f"Amplitude Shimmer   : {feats['amplitude_shimmer']}")
    print(f"Spectral Centroid   : {feats['spectral_centroid_hz']} Hz")
    print(f"Spectral Flatness   : {feats['spectral_flatness']}")
    print(f"Zero Crossing Rate  : {feats['zero_crossing_rate']}")
    print(f"Biometric Template  : 192 dimensions (L2 Norm: {round(float(sum(embedding**2)**0.5), 3)})\n")


def cmd_detect_deepfake(args):
    path = Path(args.file)
    if not path.exists():
        print(f"Error: File {path} does not exist.")
        sys.exit(1)

    with open(path, "rb") as f:
        audio_bytes = f.read()

    signal, sr = preprocess_audio(audio_bytes)
    report = detect_deepfake(signal, sr)

    print(f"\n🛡️ Deepfake & Anti-Spoofing Report: {path.name}")
    print("=" * 55)
    print(f"Verdict              : {report['verdict']}")
    print(f"Synthetic Probability: {report['synthetic_score_percent']}%")
    print(f"Risk Level           : {report['risk_level']}")
    print(f"Is Synthetic / Spoof : {'🚨 YES (SPOOF)' if report['is_synthetic'] else '✅ NO (NATURAL)'}")
    print("\nForensic Markers:")
    for k, v in report['forensic_breakdown'].items():
        print(f"  - {k:<28}: {v}")
    print(f"\nAction Recommendation:\n  {report['recommendation']}\n")


def cmd_synthesize(args):
    text = args.text
    out_path = Path(args.output)
    pitch = args.pitch

    print(f"\n🤖 Synthesizing Formant Speech...")
    print(f"Text   : \"{text}\"")
    print(f"Pitch  : {pitch} Hz")

    wav_bytes = clone_speaker_voice(
        text=text,
        target_pitch_f0=pitch,
        is_vocoded_deepfake=not args.natural
    )
    with open(out_path, "wb") as f:
        f.write(wav_bytes)

    print(f"✅ Generated audio saved to: {out_path} ({len(wav_bytes)} bytes)\n")


def main():
    parser = argparse.ArgumentParser(
        prog="aadhaar-voice",
        description="AadhaarVoice CLI: Voice Biometrics, Deepfake Detection, and Identity Tools."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # generate-vid
    p_gen = subparsers.add_parser("generate-vid", help="Generate synthetic 12-digit demo Aadhaar VID")
    p_gen.add_argument("--prefix", default="0000", help="4-digit demo sandbox prefix (default: 0000)")

    # validate-vid
    p_val = subparsers.add_parser("validate-vid", help="Validate 12-digit VID against Verhoeff checksum")
    p_val.add_argument("vid", help="12-digit VID to validate")

    # analyze-audio
    p_ana = subparsers.add_parser("analyze-audio", help="Extract acoustic biometrics from audio file")
    p_ana.add_argument("file", help="Path to WAV audio file")

    # detect-deepfake
    p_det = subparsers.add_parser("detect-deepfake", help="Analyze audio for AI deepfake/vocoder signatures")
    p_det.add_argument("file", help="Path to WAV audio file")

    # synthesize
    p_syn = subparsers.add_parser("synthesize", help="Synthesize formant acoustic speech")
    p_syn.add_argument("--text", required=True, help="Text to synthesize")
    p_syn.add_argument("--output", default="synthesized.wav", help="Output WAV filename")
    p_syn.add_argument("--pitch", type=float, default=140.0, help="Fundamental pitch in Hz")
    p_syn.add_argument("--natural", action="store_true", help="Simulate natural jitter instead of robotic vocoder")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "generate-vid":
        cmd_generate_vid(args)
    elif args.command == "validate-vid":
        cmd_validate_vid(args)
    elif args.command == "analyze-audio":
        cmd_analyze_audio(args)
    elif args.command == "detect-deepfake":
        cmd_detect_deepfake(args)
    elif args.command == "synthesize":
        cmd_synthesize(args)


if __name__ == "__main__":
    main()
