#!/usr/bin/env python3
"""
Download audio from YouTube URLs listed in a CSV file using yt-dlp.

Usage:
  1) Edit INPUT_CSV / OUTPUT_DIR / REGISTRY_CSV below
  2) python download_youtube_audio.py
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yt_dlp
except ImportError as exc:
    raise SystemExit(
        "yt-dlp is required. Install with:\n"
        "  pip install yt-dlp"
    ) from exc

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

# --------------------------
# User settings (edit these)
# --------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_CSV = Path("links.csv")
LINK_COLUMN = "link"
SONG_NAME_COLUMN = "song_name"
ARTIST_COLUMN = "artist"
OUTPUT_DIR = Path("downloads")
REGISTRY_CSV = Path("music_registry.csv")
REGISTRY_COLUMNS = ("youtube_id", "song_name", "artist", "file_path")


def sanitize_filename(name: str) -> str:
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name).strip()
    return clean or "untitled"


def resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def read_rows(path: Path) -> list[dict[str, str]]:
    abs_path = resolve_path(path)
    if not abs_path.exists():
        return []

    rows: list[dict[str, str]] = []
    with abs_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return rows

        for row in reader:
            url = (row.get(LINK_COLUMN) or "").strip()
            song_name = (row.get(SONG_NAME_COLUMN) or "").strip()
            artist = (row.get(ARTIST_COLUMN) or "").strip()
            if not url:
                continue
            rows.append({"url": url, "song_name": song_name, "artist": artist})
    return rows


def validate_columns(path: Path) -> bool:
    abs_path = resolve_path(path)
    if not abs_path.exists():
        return False
    with abs_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return False
        fieldnames = {name.strip() for name in reader.fieldnames}
    return LINK_COLUMN in fieldnames and SONG_NAME_COLUMN in fieldnames


def load_registry(path: Path) -> dict[str, dict[str, str]]:
    abs_path = resolve_path(path)
    if not abs_path.exists():
        return {}

    registry: dict[str, dict[str, str]] = {}
    with abs_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            youtube_id = (row.get("youtube_id") or "").strip()
            if not youtube_id:
                continue
            registry[youtube_id] = {
                "youtube_id": youtube_id,
                "song_name": (row.get("song_name") or "").strip(),
                "artist": (row.get("artist") or "").strip(),
                "file_path": (row.get("file_path") or "").strip(),
            }
    return registry


def write_registry_atomic(path: Path, registry: dict[str, dict[str, str]]) -> None:
    abs_path = resolve_path(path)
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = abs_path.with_suffix(abs_path.suffix + ".tmp")

    with temp_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(REGISTRY_COLUMNS))
        writer.writeheader()
        for youtube_id in sorted(registry):
            row = registry[youtube_id]
            writer.writerow(
                {
                    "youtube_id": row.get("youtube_id", ""),
                    "song_name": row.get("song_name", ""),
                    "artist": row.get("artist", ""),
                    "file_path": row.get("file_path", ""),
                }
            )

    temp_path.replace(abs_path)


def resolve_video_info(url: str) -> dict[str, str] | None:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info: dict[str, Any] | None = ydl.extract_info(url, download=False)
        except Exception:
            return None

    if not info:
        return None

    youtube_id = str(info.get("id") or "").strip()
    title = str(info.get("title") or "").strip()
    if not youtube_id:
        return None
    return {"youtube_id": youtube_id, "title": title}


def download_audio(url: str, output_dir: Path, filename_stem: str) -> Path | None:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(filename_stem)
    expected_path = output_dir / f"{safe_name}.mp3"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(output_dir / f"{safe_name}.%(ext)s"),
        "ignoreerrors": True,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            code = ydl.download([url])
        except Exception:
            return None
    if code != 0 or not expected_path.exists():
        return None
    return expected_path


def registry_file_exists(file_path: str) -> bool:
    if not file_path:
        return False
    p = Path(file_path)
    if p.is_absolute():
        return p.exists()
    return (PROJECT_ROOT / p).exists()


def to_relative_path(path: Path) -> str:
    return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))


def process_rows(rows: list[dict[str, str]]) -> tuple[int, int]:
    output_dir = resolve_path(OUTPUT_DIR)
    registry = load_registry(REGISTRY_CSV)
    seen_ids: set[str] = set()

    failures = 0
    duplicates_in_input = 0
    downloaded = 0
    skipped_existing = 0
    redownloaded_missing = 0
    metadata_failures = 0

    iterator = rows
    if tqdm is not None:
        iterator = tqdm(rows, desc="Processing tracks", unit="track")

    for row in iterator:
        url = row["url"]
        input_song_name = row["song_name"]
        input_artist = row.get("artist", "")
        info = resolve_video_info(url)
        if info is None:
            metadata_failures += 1
            failures += 1
            print(f"Failed metadata: {url}")
            continue

        youtube_id = info["youtube_id"]
        resolved_title = info["title"]
        final_song_name = input_song_name or resolved_title or youtube_id
        file_stem = f"{final_song_name} [{youtube_id}]"

        if youtube_id in seen_ids:
            duplicates_in_input += 1
            continue
        seen_ids.add(youtube_id)

        existing = registry.get(youtube_id)
        if existing and registry_file_exists(existing.get("file_path", "")):
            skipped_existing += 1
            if input_song_name:
                existing["song_name"] = input_song_name
            if input_artist:
                existing["artist"] = input_artist
            continue

        downloaded_path = download_audio(url, output_dir, file_stem)
        if downloaded_path is None:
            failures += 1
            print(f"Failed download: {url}")
            continue

        rel_path = to_relative_path(downloaded_path)
        registry[youtube_id] = {
            "youtube_id": youtube_id,
            "song_name": final_song_name,
            "artist": input_artist,
            "file_path": rel_path,
        }
        if existing:
            redownloaded_missing += 1
        else:
            downloaded += 1

    write_registry_atomic(REGISTRY_CSV, registry)

    print(f"Downloaded new: {downloaded}")
    print(f"Re-downloaded missing files: {redownloaded_missing}")
    print(f"Skipped existing: {skipped_existing}")
    print(f"Duplicate IDs in input skipped: {duplicates_in_input}")
    print(f"Metadata failures: {metadata_failures}")
    return failures, len(registry)


def main() -> int:
    input_path = resolve_path(INPUT_CSV)
    if not input_path.exists():
        print(f"Input CSV not found: {input_path}", file=sys.stderr)
        return 2

    if not validate_columns(INPUT_CSV):
        print(
            f"Input CSV missing required columns: '{LINK_COLUMN}', '{SONG_NAME_COLUMN}'.",
            file=sys.stderr,
        )
        return 2

    rows = read_rows(INPUT_CSV)
    if not rows:
        print("No valid rows found in input CSV.", file=sys.stderr)
        return 2

    failures, registry_count = process_rows(rows)
    print(f"Registry entries: {registry_count}")
    print(f"Registry saved to: {resolve_path(REGISTRY_CSV)}")
    if failures:
        print(f"Finished with {failures} failed item(s).")
        return 1

    print(f"Done. Saved audio files to: {resolve_path(OUTPUT_DIR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
