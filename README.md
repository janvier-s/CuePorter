# CuePorter

**Convert Mixed in Key hot cues to Serato format for djay and Serato DJ**

CuePorter is a macOS app that batch-converts Mixed in Key cue points into native Serato Markers2 tags, so your hot cues show up automatically in djay and Serato DJ—no need to manually load each track in Serato.

![CuePorter ScreenShot](https://files.catbox.moe/g02kvm.png)
## Features

- ✅ **Batch conversion** – Process entire folders (and subfolders) in one go
- ✅ **Two color modes:**
  - **Default djay colors** – Maps cues 1–8 to djay's default pad colors
  - **Energy-based colors** – Uses Mixed in Key's "Energy" ratings for a cool→hot gradient
- ✅ **Preserves original cue names** – Custom labels carry over; generic "ENERGY X" labels become "CUE #" in djay mode
- ✅ **Progress tracking** – Live activity log shows which files were updated and which were skipped
- ✅ **Supports FLAC, MP3, AIFF** – The formats where Serato Markers2 tags work reliably

## Requirements

- App works on macOS (tested on Apple Silicon; should work on Intel)
- Source code works on all platforms
- Your audio files must already have Mixed in Key cue point tags

## Installation

1. Download the latest `CuePorter-macOS.zip` from [Releases](../../releases)
2. Unzip and move `CuePorter.app` to your Applications folder
3. **First time:** Right-click → **Open** to bypass Gatekeeper (the app isn't code-signed)
4. If that fails, they can go to  
   System Settings → Privacy & Security → Security,  
   and click Open Anyway next to the “CuePorter” warning.
5. After that, double-click normally

## Usage

1. Launch CuePorter
2. Select your music folder
3. Choose a color mode (djay colors or energy-based)
4. Click **Start Conversion**
5. The app will scan for audio files with Mixed in Key tags and convert them

### ⚠️ Important: Back Up Your Music First

CuePorter **modifies your audio file metadata**. While it doesn't touch the actual audio data, back up your library before running it (or test on a small folder first).

If djay is currently running, quit and reopen it after conversion so it picks up the new cue points.

## Technical Details

- **Supported formats:** FLAC, MP3, AIFF (formats where Serato Markers2 tags are well-documented)
- **Built with:** Python 3.13, Tkinter, [mutagen](https://github.com/quodlibet/mutagen), [serato-tools](https://github.com/Holzhaus/serato-tools)
- **CLI version:** The repository also includes `convert_cues.py` for command-line batch conversion

## Building from Source (for Windows and Linux)

```bash
# Install dependencies
pip install mutagen serato-tools pillow pyinstaller

# Build the macOS app
pyinstaller --windowed --name "CuePorter" convert_cues_gui.py

# The .app will be in dist/CuePorter.app
```

## FAQ

**Q: Will this work with Serato DJ?**  
A: Yes. The converted tags are native Serato Markers2, so they work in both djay and Serato DJ.

**Q: What happens to files without Mixed in Key tags?**  
A: They're skipped (no changes made).

**Q: Can I undo the conversion?**  
A: Not automatically. Restore from your backup, or re-analyze in Mixed in Key.

**Q: Why doesn't it support WAV/OGG/M4A?**  
A: The Serato Markers2 tagging format varies by container, and I've only implemented the well-documented cases (FLAC/MP3/AIFF) to avoid corrupting metadata. WAV support may be added in the future.

**Q: Why does macOS say it's from an "unidentified developer"?**  
A: I don't have an Apple Developer ID. Right-click → **Open** the first time, or go to System Settings → Privacy & Security → **Open Anyway**.

## License

MIT License – see [LICENSE](LICENSE) for details.

## Acknowledgments

- [serato-tools](https://github.com/Holzhaus/serato-tools) by @Holzhaus for reverse-engineering Serato's tag format
- [mutagen](https://github.com/quodlibet/mutagen) for audio metadata handling

## Contributing

Issues and pull requests welcome! If you encounter a bug or have a feature request, please open an issue.

---

Vibe coded with [Warp](https://app.warp.dev/referral/XNMDEW) for DJs who love automation.
