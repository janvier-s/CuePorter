import os
import base64
import json
import struct
import sys
import re
from mutagen import File
from serato_tools.track_cues_v2 import TrackCuesV2

# --- Serato Markers v2 helpers ---
# FLAC stores Serato Markers2 as a base64-encoded GEOB payload.
FLAC_SERATO_HEADER = b"application/octet-stream\x00\x00Serato Markers2\x00"

# --- COLOR MAPPING ---
# Map hot cue index (1–8) to a Serato cue color progression that mimics
# djay's default pad colors (roughly: red, orange, blue, yellow, green,
# magenta, cyan, purple) without repeating colors.
DJAY_INDEX_TO_CUECOLOR = {
    1: TrackCuesV2.CueColors.RED,
    2: TrackCuesV2.CueColors.ORANGE,
    3: TrackCuesV2.CueColors.BLUE1,
    4: TrackCuesV2.CueColors.YELLOW,
    5: TrackCuesV2.CueColors.LIMEGREEN2,
    6: TrackCuesV2.CueColors.MAGENTA,
    7: TrackCuesV2.CueColors.CYAN,
    8: TrackCuesV2.CueColors.PURPLE1,
}

# Map Mixed in Key "Energy" levels (1–8) to a cool→hot gradient.
ENERGY_TO_CUECOLOR = {
    "1": TrackCuesV2.CueColors.BLUE1,
    "2": TrackCuesV2.CueColors.BLUE2,
    "3": TrackCuesV2.CueColors.CYAN,
    "4": TrackCuesV2.CueColors.LIMEGREEN2,
    "5": TrackCuesV2.CueColors.YELLOW,
    "6": TrackCuesV2.CueColors.YELLOWORANGE,
    "7": TrackCuesV2.CueColors.ORANGE,
    "8": TrackCuesV2.CueColors.RED,
}


def build_serato_entries_from_mik(mik_cues, color_mode: str = "djay"):
    """Convert MIK cue JSON into TrackCuesV2 entries.

    Serato uses integer milliseconds for the cue position ("position" field).
    """
    entries = []

    # Track color (optional) - keep it simple and use white.
    entries.append(TrackCuesV2.ColorEntry(b"\x00", TrackCuesV2.TrackColors.WHITE.value))

    # Only first 8 cues are supported as hot cues.
    for idx, cue in enumerate(mik_cues[:8]):
        cue_index = idx + 1  # 1–8 for humans / djay-style pads

        original_name = (cue.get("name", "") or "").strip()

        if color_mode == "energy":
            # Preserve or normalize Mixed in Key "Energy" labels.
            # Try to extract the energy level from the name, e.g. "Energy 7".
            energy_level = None
            if original_name:
                parts = original_name.upper().split()
                if parts[0] == "ENERGY" and len(parts) > 1:
                    energy_level = parts[1]
            if energy_level is None:
                energy_level = "8"  # default to highest if unknown

            name = original_name or f"Energy {energy_level}"
            color_enum = ENERGY_TO_CUECOLOR.get(energy_level, TrackCuesV2.CueColors.RED)
        else:
            # djay-style: rename generic "ENERGY X" labels to simple "CUE #".
            if original_name.upper().startswith("ENERGY"):
                name = f"CUE {cue_index}"
            else:
                name = original_name or f"CUE {cue_index}"

            # Map by cue index, not by MIK "energy" field, to match djay's palette.
            color_enum = DJAY_INDEX_TO_CUECOLOR.get(
                cue_index, TrackCuesV2.CueColors.RED
            )

        color_bytes = color_enum.value

        # MIK time is already in milliseconds; Serato stores integer ms.
        # Some versions of MIK can store slightly negative times for the first
        # cue (e.g. -29ms). Serato's Markers2 format expects an *unsigned*
        # 32‑bit integer here, so we clamp into the valid range.
        raw_time = cue.get("time", 0) or 0
        try:
            pos_ms = int(round(float(raw_time)))
        except (TypeError, ValueError):
            pos_ms = 0
        # Clamp to [0, 2^32-1]
        if pos_ms < 0:
            pos_ms = 0
        elif pos_ms > 0xFFFFFFFF:
            pos_ms = 0xFFFFFFFF

        entries.append(
            TrackCuesV2.CueEntry(
                b"\x00",  # field1 (constant)
                idx,  # index 0-7
                pos_ms,  # position in ms
                b"\x00",  # field4 (constant)
                color_bytes,  # 3-byte color
                b"\x00\x00",  # field6 (constant)
                name,  # visible cue name
            )
        )

    # Add BPM lock entry (disabled).
    entries.append(TrackCuesV2.BpmLockEntry(False))
    return entries


def write_serato_markers_v2(
    audio,
    filepath,
    mik_cues,
    color_mode: str = "djay",
    overwrite: bool = False,
    log_fn=None,
):
    """Write proper Serato Markers2 data so djay/Serato can read the cues.

    For FLAC: store a base64-encoded GEOB body in SERATO_MARKERS_V2.
    For MP3/AIFF: write a real GEOB frame via serato-tools.
    """
    entries = build_serato_entries_from_mik(mik_cues, color_mode=color_mode)
    ext = os.path.splitext(filepath)[1].lower()

    # FLAC path: Vorbis comment with base64 of GEOB payload.
    if ext == ".flac":
        # Check for existing markers
        if not overwrite and "serato_markers_v2" in audio:
            msg = (
                "Skipping: Existing Serato markers found (use --overwrite to replace)."
            )
            if log_fn:
                log_fn(msg)
            else:
                print("   -", msg)
            return False

        tags = TrackCuesV2.__new__(TrackCuesV2)  # bypass __init__
        tags.raw_data = None
        tags.entries = entries
        tags.modified = True
        TrackCuesV2._dump(tags)
        raw = tags.raw_data

        geob_bytes = FLAC_SERATO_HEADER + raw
        comment_val = base64.b64encode(geob_bytes).decode("ascii")

        # Explicitly remove existing tag if overwriting
        if "serato_markers_v2" in audio:
            del audio["serato_markers_v2"]

        audio["serato_markers_v2"] = comment_val
        audio.save()
        return True

    # MP3 / AIFF path: let serato-tools write a proper GEOB frame.
    if ext in (".mp3", ".aif", ".aiff"):
        try:
            # serato-tools requires the filepath for these formats
            tags = TrackCuesV2(filepath)

            # Check for existing entries
            if not overwrite and tags.entries:
                msg = "Skipping: Existing Serato markers found (use --overwrite to replace)."
                if log_fn:
                    log_fn(msg)
                else:
                    print("   -", msg)
                return False

        except Exception as e:
            msg = f"Unable to open Serato tags for '{os.path.basename(filepath)}': {e}"
            if log_fn:
                log_fn(msg)
            else:
                print("   - ERROR:", msg)
            return False

        tags.entries = entries
        tags.modified = True
        tags._dump()
        tags.save()
        return True

    # Other formats (wav, m4a, mp4, etc.) are not handled here.
    msg = (
        f"Skipping unsupported format for Serato Markers2 for "
        f"'{os.path.basename(filepath)}'."
    )
    if log_fn:
        log_fn(msg)
    else:
        print("   -", msg)
    return False


def process_track(
    filepath, color_mode: str = "djay", overwrite: bool = False, log_fn=None
):
    def _log(msg: str):
        if log_fn:
            log_fn(msg)
        else:
            print(msg)

    try:
        audio = File(filepath)
        if audio is None:
            _log(f"ERROR: Could not open file '{os.path.basename(filepath)}'.")
            return False

        mik_tag_key = None
        # Mixed In Key uses different tag names for different file types
        # e.g., 'TXXX:CUEPOINTS' for MP3, 'CUEPOINTS' for M4A.
        for key in audio.keys():
            if "cuepoints" in key.lower():
                mik_tag_key = key
                break

        if not mik_tag_key:
            # Silently skip files without MIK tags
            _log("No Mixed in Key cuepoints tag found.")
            return False

        _log(f"-> Processing: {os.path.basename(filepath)}")

        # Mixed In Key may store cue data in different tag types:
        # - ID3 TXXX/CUEPOINTS (text frame, often list-like)
        # - MP4/other formats as a simple string
        # - ID3 GEOB:CuePoints (binary GEOB frame containing a base64 string)
        # Handle these cases robustly and always end up with the base64 text.
        mik_tag = audio[mik_tag_key]

        # Extract the raw value from the tag in a tolerant way
        if isinstance(mik_tag, (list, tuple)):
            raw_val = mik_tag[0]
        elif hasattr(mik_tag, "text"):
            # ID3 text frame (e.g. TXXX)
            raw_val = mik_tag.text[0] if mik_tag.text else ""
        elif hasattr(mik_tag, "data"):
            # GEOB frame (e.g. GEOB:CuePoints)
            raw_val = mik_tag.data
        else:
            raw_val = mik_tag

        # Normalise to a string that should contain base64 JSON
        if isinstance(raw_val, bytes):
            raw_str = raw_val.decode("utf-8", errors="ignore")
        else:
            raw_str = str(raw_val)

        # Some tags store the JSON directly, some store base64-encoded JSON.
        # Try base64 first; if that doesn't look like JSON, fall back to raw.
        mik_bytes = None
        try:
            candidate = base64.b64decode(raw_str)
            if candidate.lstrip().startswith(b"{"):
                mik_bytes = candidate
        except Exception:
            mik_bytes = None

        if mik_bytes is None:
            mik_bytes = raw_str.encode("utf-8", errors="ignore")

        mik_cues = json.loads(mik_bytes).get("cues", [])

        if not mik_cues:
            _log("No cues found in Mixed in Key tag; skipping write.")
            return False

        if write_serato_markers_v2(
            audio,
            filepath,
            mik_cues,
            color_mode=color_mode,
            overwrite=overwrite,
            log_fn=_log,
        ):
            _log(f"SUCCESS: Converted {len(mik_cues)} cue points.")
            return True

        return False

    except Exception as e:
        _log(f"ERROR processing file '{os.path.basename(filepath)}': {e}")
        return False


# --- Main Execution ---
if __name__ == "__main__":
    print("--- MIK Cue to Serato Cue Converter (Corrected Colors) ---")
    print("🔴 WARNING: This script modifies your files. BACKUP YOUR MUSIC FIRST. 🔴\n")

    import argparse

    parser = argparse.ArgumentParser(
        description="Convert Mixed In Key cues to Serato markers."
    )
    parser.add_argument("path", nargs="?", help="Music folder path")
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing Serato markers"
    )
    parser.add_argument(
        "--color-mode", default="djay", choices=["djay", "energy"], help="Color mode"
    )
    args = parser.parse_args()

    if args.path:
        target_path = args.path
    else:
        target_path = input("Enter the full path to your music folder: ")

    if not os.path.isdir(target_path):
        print("Error: The path provided is not a valid directory.")
        exit()

    supported_extensions = (".mp3", ".flac", ".aif", ".aiff")
    processed_count = 0
    skipped_count = 0

    print(f"\\nScanning '{target_path}' for music files...")

    all_files = []
    for root, dirs, files in os.walk(target_path):
        for filename in files:
            # Skip macOS metadata files (._*)
            if filename.startswith("._"):
                continue
            if filename.lower().endswith(supported_extensions):
                all_files.append(os.path.join(root, filename))

    total_files = len(all_files)
    print(f"Found {total_files} supported files to check.")

    for i, filepath in enumerate(all_files):
        filename = os.path.basename(filepath)
        cli_messages = []

        def cli_log(msg: str, _filename=filename):
            cli_messages.append(msg)

        success = process_track(
            filepath,
            color_mode=args.color_mode,
            overwrite=args.overwrite,
            log_fn=cli_log,
        )

        status = "SUCCESS" if success else "SKIPPED"
        detail = None

        # Try to extract cue count from success message
        for m in cli_messages:
            if "SUCCESS: Wrote" in m:
                m_no_commas = m.replace(",", "")
                match = re.search(r"Wrote (\\d+) cue points", m_no_commas)
                if match:
                    detail = f"{match.group(1)} cue points"
                else:
                    detail = m.replace("SUCCESS: ", "").strip()
                status = "SUCCESS"
                break

        if not success:
            if any("No Mixed in Key cuepoints tag found" in m for m in cli_messages):
                status = "SKIPPED"
                detail = "No Mixed in Key cuepoints tag found; skipping."
            elif any("No cues found in Mixed in Key tag" in m for m in cli_messages):
                status = "SKIPPED"
                detail = "No Mixed in Key cues found; skipping."
            elif any("Skipping unsupported format" in m for m in cli_messages):
                status = "SKIPPED"
                detail = "Unsupported format; skipping."
            elif any("ERROR" in m for m in cli_messages):
                status = "ERROR"
                # Show first error message verbatim
                detail = next(m for m in cli_messages if "ERROR" in m)

        if not detail:
            # Fallback: join all messages if we couldn't classify
            detail = "; ".join(cli_messages) if cli_messages else "No changes made."

        print(f"[{i+1}/{total_files}] {filename} -> {status}: {detail}")

        if success:
            processed_count += 1
        else:
            skipped_count += 1

    print(
        "\nConversion complete. "
        f"{processed_count} files updated, {skipped_count} skipped (out of {total_files})."
    )
