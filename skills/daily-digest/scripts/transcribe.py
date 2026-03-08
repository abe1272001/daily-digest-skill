#!/usr/bin/env python3
"""Transcribe audio files using faster-whisper."""

import argparse
import sys


def transcribe(
    audio_path: str,
    model_size: str = "tiny",
    language: str = "zh",
    device: str = "cpu",
) -> str:
    """Transcribe audio file and return text."""
    from faster_whisper import WhisperModel

    print(f"Loading whisper model: {model_size} ({device})", file=sys.stderr)
    model = WhisperModel(model_size, device=device, compute_type="int8")

    print(f"Transcribing: {audio_path}", file=sys.stderr)
    segments, info = model.transcribe(
        audio_path,
        language=language,
        vad_filter=True,  # Filter out silence for cleaner output
    )

    texts = []
    for segment in segments:
        texts.append(segment.text.strip())

    transcript = " ".join(texts)
    print(
        f"Transcription complete: {len(transcript)} chars, "
        f"language={info.language} (prob={info.language_probability:.2f})",
        file=sys.stderr,
    )

    return transcript


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio with faster-whisper")
    parser.add_argument("--audio", required=True, help="Path to audio file")
    parser.add_argument(
        "--model",
        default="tiny",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="Whisper model size (default: tiny)",
    )
    parser.add_argument(
        "--language", default="zh", help="Language code (default: zh)"
    )
    parser.add_argument(
        "--device", default="cpu", choices=["cpu", "cuda"], help="Compute device"
    )
    args = parser.parse_args()

    transcript = transcribe(args.audio, args.model, args.language, args.device)
    # Output transcript to stdout for pipeline consumption
    print(transcript)


if __name__ == "__main__":
    main()
