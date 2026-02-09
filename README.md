<p align="center">
  <img src="https://img.shields.io/badge/STATUS-BETA-yellow?style=for-the-badge" alt="Beta Status"/>
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/Gemini-Vision_AI-red?style=for-the-badge&logo=google" alt="Gemini"/>
</p>

# 🎮 Xayk Noob's Journal

**AI-powered overlay assistant for retro games.** Uses Google's Gemini Vision to analyze your game screen in real-time and provide contextual guidance from walkthroughs.

> ⚠️ **This project is currently in BETA.** Many features are still being developed and improved. Contributions and feedback are welcome!

---

## 📸 Preview

<p align="center">
  <i>Screenshot coming soon...</i>
</p>

---

## 🚀 How to Use

### Requirements

| Requirement | Description |
|-------------|-------------|
| **Python 3.10+** | [Download here](https://www.python.org/downloads/) |
| **Gemini API Key** | Free at [Google AI Studio](https://aistudio.google.com/app/apikey) |

### Installation (Windows)

1. **Clone or download** this repository

2. **Run the installer**
   
   Double-click `install.bat` and wait for completion.

3. **Configure your API key**
   
   Open the `.env` file created in the project folder:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```
   
   Replace `your_api_key_here` with your actual Gemini API key.

4. **Start the application**
   
   Double-click `run.bat`

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/xayk-noobs-journal.git
cd xayk-noobs-journal

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate          # Windows
source venv/bin/activate         # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Setup environment
copy env.example .env            # Windows
cp env.example .env              # Linux/Mac

# Edit .env and add your GEMINI_API_KEY

# Run
python main.py
```

---

## ⚙️ How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Your Game     │────▶│  Screen Capture  │────▶│  Gemini Vision  │
│   (Emulator)    │     │   (PIL/mss)      │     │   Analysis      │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
┌─────────────────┐     ┌──────────────────┐              │
│    Overlay      │◀────│   Task/Context   │◀─────────────┘
│  (PyQt6 UI)     │     │   Generation     │
└─────────────────┘     └──────────────────┘
```

### The Pipeline

1. **Screen Capture** → Captures your game screen at regular intervals (default: 15s)

2. **AI Vision Analysis** → Sends the screenshot to Gemini Vision API, which understands:
   - Current location in the game
   - What's happening on screen
   - UI elements, characters, environment

3. **Knowledge Base Query** → Searches the local game guides for relevant context based on the visual analysis

4. **Task Generation** → Combines the visual analysis with guide knowledge to generate your next objective

5. **Overlay Display** → Shows the task in a non-intrusive retro-styled overlay

### Overlay Controls

| Action | Result |
|--------|--------|
| **Drag** | Move the overlay anywhere |
| **Click `─`** | Minimize to compact bar |
| **Click bar** | Expand overlay |
| **🟡 Yellow dot** | New task available! |

---

## 📁 Adding Game Guides

Place your game walkthrough files in the `guides/` folder.

**Supported format:** `.txt` files

After adding new guides:
```bash
python main.py --mode reindex
```

---

## 🎮 Tested Emulators

- ✅ PCSX2 (PS2)
- ✅ DuckStation (PS1)
- ✅ RetroArch
- Should work with any windowed game!

---

## ⚠️ Known Limitations (Beta)

- **API Rate Limits**: Free Gemini tier allows ~15 requests/minute
- **Visual Recognition**: Works best with games that have clear visual cues
- **Guide Quality**: Results depend on the quality of your walkthrough files
- **Language**: Currently optimized for English guides

---

## 🛠️ Roadmap

- [ ] Multi-language support
- [ ] Better guide parsing
- [ ] Custom overlay themes
- [ ] Hotkey support
- [ ] Game auto-detection
- [ ] Local LLM option (no API needed)

---

## 🤝 Contributing

This project is in **active development**! We welcome:

- 🐛 Bug reports
- 💡 Feature suggestions
- 📝 Game guide contributions
- 🔧 Code improvements

Feel free to open an issue or submit a pull request!

---

## 📝 License

MIT License - feel free to use and modify!

---

<p align="center">
  Made with ❤️ for retro gaming enthusiasts
  <br><br>
  <a href="https://github.com/YOUR_USERNAME/xayk-noobs-journal/issues">Report Bug</a>
  ·
  <a href="https://github.com/YOUR_USERNAME/xayk-noobs-journal/issues">Request Feature</a>
</p>
