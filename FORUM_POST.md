# CuePorter – Convert Mixed in Key Cues to Serato Format (for djay)

Hey everyone! 👋

I've built a free macOS app called **CuePorter** that solves a common workflow issue: **getting Mixed in Key hot cues to actually show up in djay (and Serato)**.

## The Problem

If you use Mixed in Key to analyze tracks and set hot cues, those cues are stored in a proprietary format that djay and Serato can't read directly. You have to manually load each track in Serato DJ to convert the tags, which is tedious if you have hundreds or thousands of files.

## The Solution

**CuePorter** converts Mixed in Key cue points into proper **Serato Markers2** tags that djay and Serato DJ can read natively. Just point it at your music folder and it'll batch-process everything.

### Features

- ✅ **Batch conversion** – Process entire folders (and subfolders) in one go
- ✅ **Two color modes:**
  - **Default djay colors** – Maps cues 1–8 to djay's default pad colors (red, orange, blue, yellow-orange, green, magenta, cyan, purple)
  - **Energy-based colors** – Uses Mixed in Key's "Energy" ratings to create a cool→hot gradient (blues/greens for low energy, oranges/reds for high)
- ✅ **Preserves original cue names** – If your MIK cues have custom labels, they'll carry over (generic "ENERGY X" labels get renamed to "CUE #" in djay mode)
- ✅ **Progress tracking** – Live activity log shows which files were updated and which were skipped
- ✅ **Supports FLAC, MP3, AIFF** – The formats djay and Serato both handle well

### What It Doesn't Do

- ❌ **No automatic grid/beatgrid conversion** – Only hot cues are converted
- ❌ **Not a file manager** – It modifies metadata tags in-place; it doesn't move or rename files

## How to Use

1. **Download** `CuePorter-macOS.zip` (link below)
2. **Unzip** and move `CuePorter.app` to your Applications folder (or anywhere you like)
3. **Open the app:**
   - First time: Right-click → **Open** to bypass Gatekeeper (the app isn't code-signed since I don't have an Apple Developer account)
   - After that you can just double-click it normally
4. **Select your music folder** and choose a color mode
5. **Click "Start Conversion"** – The app will scan for audio files with Mixed in Key tags and convert them

### ⚠️ Important: Back Up Your Music First

This app **modifies your audio file metadata**. While it doesn't touch the actual audio data, I strongly recommend backing up your music library before running it (or test on a small folder first).

If djay is currently running when you convert files, you'll need to quit and reopen djay for it to pick up the new cue points.

## Technical Details

- **Supported formats:** MP3, FLAC, AIFF (the formats where Serato Markers2 tags work reliably)
- **Requirements:** macOS (tested on Apple Silicon, should work on Intel too)
- **Dependencies:** Python 3.13 + mutagen + serato-tools (all bundled in the .app)
- **Source code:** Available on request (it's a Python/Tkinter GUI that wraps the `serato-tools` library)

## Download

[**Download CuePorter-macOS.zip**](#) *(attach your zip file here or upload to GitHub Releases / Google Drive / Dropbox)*

---

## FAQ

**Q: Will this work with Serato DJ?**  
A: Yes! The converted tags are native Serato Markers2, so they'll show up in Serato DJ as well.

**Q: What happens to files that don't have Mixed in Key tags?**  
A: They're skipped (no changes made).

**Q: Can I undo the conversion?**  
A: Not automatically. The app overwrites the Serato Markers2 tag. If you have a backup, you can restore the originals. Otherwise you'd need to re-analyze in Mixed in Key.

**Q: Why does macOS say the app is from an "unidentified developer"?**  
A: I don't have an Apple Developer ID to code-sign the app. You can bypass this by right-clicking the app and choosing **Open** the first time (or go to System Settings → Privacy & Security → click "Open Anyway").

**Q: Does this work on Windows?**  
A: Not yet (this is macOS-only for now). If there's demand I could build a Windows version.

---

Hope this helps streamline your workflow! Let me know if you run into any issues or have feature requests. 🎧

– Janvier
