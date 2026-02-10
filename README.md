<p align="center">
  <img src="https://img.shields.io/badge/STATUS-BETA-yellow?style=for-the-badge" alt="Beta Status"/>
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/Ollama-Local_LLM-green?style=for-the-badge" alt="Ollama"/>
  <img src="https://img.shields.io/badge/Gemini-Vision_AI-red?style=for-the-badge&logo=google" alt="Gemini"/>
</p>

# Xayk Noob's Journal

An overlay assistant for retro games that uses AI vision to analyze your screen and provide guidance. Works with local LLMs (Ollama) for unlimited use, or cloud AI (Gemini).

> **Note:** This project is in beta. Some features are still being developed.

---

## Preview

<p align="center">
  <img src="assets/Select MODE.png" alt="Mode Selection" width="700"/>
  <br>
  <em>Launcher - Choose between Journal and Guide mode</em>
</p>

<p align="center">
  <img src="assets/GUIDE MODE.png" alt="Guide Mode" width="700"/>
  <br>
  <em>Guide Mode - AI-powered instructions overlay</em>
</p>

<p align="center">
  <img src="assets/Journal with sections.png" alt="Journal Mode" width="700"/>
  <br>
  <em>Journal Mode - Manual notes with categories, timestamps, and export</em>
</p>

---

## Features

- **Two Modes**: Journal (manual notes) and Guide (AI-powered hints)
- **Local LLM Support (Ollama)** - No API limits, runs completely offline
- **Session Memory** - Remembers your progress, AI observations, and notes across play sessions
- **Journal with Categories** - Organize notes as Items, Locations, Objectives, or Notes with timestamps
- **Smart Guide** - Detects when you're stuck and gives more specific hints
- **Auto Game Detection** - Matches emulator window title with your game guides
- **Export Notes** - Save your journal entries to a text file organized by category
- **Note Persistence** - All journal notes are saved to disk and restored on next session
- **Minimizable Overlay** - Non-intrusive retro-styled UI

---

## What's New (Latest Update)

### Journal Mode Improvements
- **Category Filters** - Filter notes by type: ALL / NOTES / ITEMS / LOCS / OBJS
- **Timestamps** - Every entry shows when it was created
- **Type Selector** - Choose between Note, Item, Location, or Objective when adding entries
- **Export to File** - Export all notes to `exports/` folder, organized by category
- **Full Persistence** - Notes are saved automatically and restored when you reopen the journal

### Smarter Guide Mode
- **Analysis History** - AI remembers the last 10 observations to avoid repeating itself
- **Stuck Detection** - If you're in the same area for too long, the AI gives more specific hints
- **Contextual Search** - Knowledge base searches now use your current location, objective, and recent history
- **Tips Memory** - Tips given are saved to avoid repetition across the session

### Auto Game Detection
- Matches the emulator window title (e.g. "PCSX2 - Metal Gear Solid 2") with available guides
- Supports abbreviation matching (MGS2, RE2, SH, FF, DMC, KH, etc.)

### Cross-Session Memory
- AI observations are stored between sessions
- Stuck areas are tracked and shared with the AI for better hints
- Session summary saved on exit (where you stopped, what you were doing)
- Rich recap when you return to a game

---

## How to Use

### Requirements

| Requirement | Description |
|-------------|-------------|
| Python 3.10+ | [Download here](https://www.python.org/downloads/) |
| Ollama (recommended) | [Download here](https://ollama.ai) - Free, local, no limits |
| Gemini API Key (optional) | [Google AI Studio](https://aistudio.google.com/app/apikey) - Has rate limits |

### Option 1: With Ollama (Recommended - No Limits)

1. Install [Ollama](https://ollama.ai)

2. Pull a vision model:
   ```bash
   ollama pull llava
   ```

3. Start Ollama:
   ```bash
   ollama serve
   ```

4. Clone and run:
   ```bash
   git clone https://github.com/Luiz-Xayk/xayk-noobs-journal.git
   cd xayk-noobs-journal
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```

### Option 2: With Gemini (Cloud - Has Rate Limits)

1. Get a free API key at [Google AI Studio](https://aistudio.google.com/app/apikey)

2. Clone and configure:
   ```bash
   git clone https://github.com/Luiz-Xayk/xayk-noobs-journal.git
   cd xayk-noobs-journal
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create `.env` file:
   ```
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=your_api_key_here
   ```

4. Run:
   ```bash
   python main.py
   ```

---

## How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Your Game     │────>│  Screen Capture  │────>│   AI Vision     │
│   (Emulator)    │     │   (PIL/mss)      │     │ (Ollama/Gemini) │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                         │
┌─────────────────┐     ┌──────────────────┐             │
│    Overlay      │<────│  Session Memory  │<────────────┘
│  (PyQt6 UI)     │     │  + Knowledge DB  │
└─────────────────┘     └──────────────────┘
```

1. **Screen Capture** - Captures your game screen at regular intervals (default: 10s)

2. **Vision Analysis** - AI analyzes the screenshot to understand current location and what's happening

3. **Session Memory** - Tracks items, locations, objectives, AI observations, stuck areas, and player notes

4. **Knowledge Base** - Searches local game guides with smart contextual queries

5. **Journal / Guide** - Displays passive observations or active hints in a retro overlay

6. **Persistence** - Everything is saved to disk and restored on next session

### Journal Controls

| Action | Result |
|--------|--------|
| Type selector | Choose Note, Item, Location, or Objective |
| Filter buttons | Filter by category (ALL, NOTES, ITEMS, LOCS, OBJS) |
| Checkbox | Mark items as done (strikethrough) |
| `x` button | Delete an entry |
| Export button | Save all notes to a .txt file |

### Overlay Controls

| Action | Result |
|--------|--------|
| Drag | Move the overlay |
| Click `─` | Minimize to bar |
| Click bar | Expand overlay |
| Double-click | Toggle minimize |
| Yellow dot | New task available |

---

## Adding Game Guides

Organize guides by game folders:

```
guides/
├── MGS2/
│   └── game_data.txt
├── ResidentEvil2/
│   └── game_data.txt
├── SilentHill/
│   └── game_data.txt
└── EXAMPLE_TEMPLATE/
    └── game_data.txt    <- Use this as a template
```

After adding new guides:
```bash
python main.py --mode reindex
```

---

## Command Line Options

```bash
python main.py --help

# Use specific LLM
python main.py --llm ollama
python main.py --llm gemini

# Passive mode (no spoilers - default)
python main.py --passive

# Active mode (with hints)
python main.py --active

# Custom interval (milliseconds)
python main.py --interval 5000

# CLI mode (no overlay)
python main.py --mode cli

# Reindex guides
python main.py --mode reindex
```

---

## Session Persistence

Your progress is saved automatically in `sessions/`:
- Items found & used
- Locations visited
- Objectives completed
- Player notes (with categories and timestamps)
- AI observations memory
- Stuck areas tracking
- Session history summaries
- Play session count

When you return to a game, you'll see a rich recap of your progress.

---

## Tested Emulators

- PCSX2 (PS2)
- DuckStation (PS1)
- PPSSPP (PSP)
- Dolphin (GameCube/Wii)
- RetroArch
- Citra (3DS)
- mGBA (GBA)
- Snes9x (SNES)
- Should work with any windowed game

---

## Known Limitations

- **Gemini Rate Limits**: Free tier allows ~15 requests/minute (use Ollama for unlimited)
- **Visual Recognition**: Works best with games that have clear visual cues
- **Guide Quality**: Results depend on the quality of your game data files

---

## Roadmap

- [x] Local LLM support (Ollama)
- [x] Session persistence (save state with memory)
- [x] Passive mode (no spoilers)
- [x] Game folder structure
- [x] Journal mode with categories and checkboxes
- [x] Note persistence (save/load from disk)
- [x] Smart Guide (history, stuck detection)
- [x] Auto game detection from emulator window
- [x] Export notes to file
- [x] Cross-session AI memory
- [ ] Multi-language support
- [ ] Gameplay recording and analysis
- [ ] Custom overlay themes
- [ ] Hotkey support
- [ ] Voice narration of journal entries

---

## Contributing

Bug reports, feature suggestions, and pull requests are welcome.

---

## License

MIT License
