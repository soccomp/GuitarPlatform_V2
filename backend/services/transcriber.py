import shutil
import subprocess
import tempfile
from pathlib import Path


DEFAULT_WHISPER_MODEL = "base"
DEFAULT_WHISPER_LANGUAGE = "zh"


class TranscriptionError(RuntimeError):
    pass


def transcribe_media(
    media_path: str | Path,
    output_path: str | Path,
    model: str = DEFAULT_WHISPER_MODEL,
    language: str = DEFAULT_WHISPER_LANGUAGE,
) -> Path:
    source = Path(media_path).resolve()
    target = Path(output_path).resolve()

    if not source.exists():
        raise TranscriptionError(f"Media file not found: {source}")

    whisper_binary = shutil.which("whisper")
    if not whisper_binary:
        raise TranscriptionError("Whisper CLI is not installed on this machine.")

    with tempfile.TemporaryDirectory(prefix="gp-transcript-") as tmpdir:
        temp_dir = Path(tmpdir)
        command = [
            whisper_binary,
            str(source),
            "--model",
            model,
            "--language",
            language,
            "--task",
            "transcribe",
            "--output_dir",
            str(temp_dir),
            "--output_format",
            "txt",
        ]

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "").strip() or "Whisper transcription failed."
            raise TranscriptionError(detail) from exc

        transcript_file = temp_dir / f"{source.stem}.txt"
        if not transcript_file.exists():
            raise TranscriptionError("Whisper did not produce a transcript file.")

        content = transcript_file.read_text(encoding="utf-8").strip()
        if not content:
            raise TranscriptionError("Generated transcript is empty.")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content + "\n", encoding="utf-8")
        return target
