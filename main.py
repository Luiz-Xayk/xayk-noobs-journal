import os
import sys
import time
import base64
import io
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv
from PIL import Image

# Ensure we're in the correct directory (for .exe)
if getattr(sys, 'frozen', False):
    # Running as .exe
    app_dir = Path(sys.executable).parent
else:
    # Running as .py
    app_dir = Path(__file__).parent

os.chdir(app_dir)
load_dotenv()

from vision_engine import VisionEngine
from knowledge_base import KnowledgeBase
from session_manager import SessionManager
from overlay_ui import RetroTaskerApp
from journal_overlay import JournalApp

# Try to import Ollama (local LLM - no rate limits!)
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Try to import Gemini (cloud LLM - has rate limits)
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class RetroTasker:
    
    # Prompt for passive mode (no spoilers, just observations)
    PASSIVE_PROMPT = """You are observing a retro game screenshot from {game_name}.

PLAYER'S CURRENT STATE:
{session_state}

RECENT HISTORY:
{history}

GAME KNOWLEDGE:
{game_context}

Analyze the screenshot and provide a SHORT journal note (like a player's diary).

Rules:
- Maximum 15 words
- Be PASSIVE - describe what you SEE, not what to DO
- NO SPOILERS - don't reveal solutions or future events
- Write as observations: "Found X", "Entered Y", "Item Z nearby"
- If you see an item, just note it exists (not what it does)
- Do NOT repeat observations from recent history
- If nothing new, say "Still exploring..."
- Answer in English

JOURNAL NOTE:"""

    # Prompt for active mode (gives hints)
    ACTIVE_PROMPT = """You are a retro game assistant analyzing a screenshot from {game_name}.

PLAYER'S CURRENT STATE:
{session_state}

RECENT HISTORY (what happened before):
{history}

GAME DATA (locations, objectives, items):
{game_context}

Look at this screenshot and:
1. Identify the current location/area in the game
2. Determine what the player should do next
3. Give a concise, actionable instruction

Rules:
- Be direct and concise (maximum 20 words)
- Use action verbs (go, pick up, use, defeat, talk to, etc.)
- If you can identify the area, give specific guidance
- Do NOT repeat the same advice from recent history
- If unclear, say "Explore the area" or similar
- Answer in English
{stuck_hint}
NEXT ACTION:"""

    # Extra hint when player seems stuck
    STUCK_HINT = """
IMPORTANT: The player seems STUCK (same area for a while). Give a MORE SPECIFIC hint.
Look carefully at the screenshot for doors, items, or interactive elements they might have missed."""

    def __init__(self, 
                 emulator_title: Optional[str] = None,
                 llm_provider: str = "auto",
                 passive_mode: bool = True):
        print("=" * 60)
        print("XAYK NOOB'S JOURNAL - Initializing...")
        print("=" * 60)
        
        self.passive_mode = passive_mode
        self.llm_provider = llm_provider
        
        print("\n[1/5] Starting Vision Engine...")
        self.vision = VisionEngine()
        
        print("\n[2/5] Starting Knowledge Base...")
        self.knowledge = KnowledgeBase()
        
        print("\n[3/5] Starting Session Manager...")
        self.session = SessionManager()
        
        print("\n[4/5] Configuring LLM...")
        self._setup_llm()
        
        print("\n[5/5] Searching for emulator window...")
        if emulator_title:
            self.vision.find_emulator_window(emulator_title)
        else:
            self.vision.find_emulator_window()
        
        self.last_task = ""
        self.is_running = False
        self.analysis_history: list = []  # Last N analyses for context
        self.stuck_counter = 0  # Track repeated similar analyses
        self.current_game = self._detect_game()
        
        # Start session for detected game
        if self.current_game:
            self.session.start_session(self.current_game)
        
        print("\n" + "=" * 60)
        print("Xayk Noob's Journal ready!")
        if self.current_game:
            print(f"Game detected: {self.current_game}")
        print(f"Mode: {'Passive (no spoilers)' if passive_mode else 'Active (with hints)'}")
        print(f"LLM: {self.active_provider or 'None'}")
        print("=" * 60)
    
    def _setup_llm(self):
        """Setup LLM provider - prioritizes Ollama (local, no limits)"""
        self.gemini_client = None
        self.gemini_model = None
        self.ollama_model = None
        self.active_provider = None
        
        provider = self.llm_provider.lower()
        
        # Auto-detect best available provider
        if provider == "auto":
            if self._try_setup_ollama():
                return
            if self._try_setup_gemini():
                return
            print("No LLM available! Install Ollama or configure Gemini API key.")
        
        elif provider == "ollama":
            if not self._try_setup_ollama():
                print("Ollama not available. Install from: https://ollama.ai")
        
        elif provider == "gemini":
            if not self._try_setup_gemini():
                print("Gemini not available. Check your API key.")
    
    def _try_setup_ollama(self) -> bool:
        """Try to setup Ollama (local LLM)"""
        if not OLLAMA_AVAILABLE:
            print("Ollama package not installed. Run: pip install ollama")
            return False
        
        try:
            # Check if Ollama is running and has a vision model
            models = ollama.list()
            available_models = [m.model for m in models.get('models', [])]
            
            # Prefer vision-capable models
            vision_models = ["llava", "llava:13b", "llava:7b", "bakllava", "moondream"]
            text_models = ["llama3.2", "llama3.1", "llama3", "mistral", "phi3"]
            
            # Try vision models first
            for model in vision_models:
                for available in available_models:
                    if model in available.lower():
                        self.ollama_model = available
                        self.active_provider = f"Ollama ({available})"
                        print(f"Ollama configured with vision model: {available}")
                        return True
            
            # Fall back to text models
            for model in text_models:
                for available in available_models:
                    if model in available.lower():
                        self.ollama_model = available
                        self.active_provider = f"Ollama ({available})"
                        print(f"Ollama configured with: {available}")
                        print("Note: For better results, install a vision model: ollama pull llava")
                        return True
            
            print("No suitable Ollama model found. Run: ollama pull llava")
            return False
            
        except Exception as e:
            print(f"Ollama not running: {e}")
            print("Start Ollama with: ollama serve")
            return False
    
    def _try_setup_gemini(self) -> bool:
        """Try to setup Gemini (cloud LLM)"""
        if not GEMINI_AVAILABLE:
            return False
        
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return False
        
        try:
            self.gemini_client = genai.Client(api_key=api_key)
            self.gemini_model = "gemini-2.0-flash"
            self.active_provider = "Gemini (cloud)"
            print("Gemini Vision configured!")
            print("Warning: Cloud API has rate limits. Consider using Ollama for unlimited local processing.")
            return True
        except Exception as e:
            print(f"Error configuring Gemini: {e}")
            return False
    
    def _detect_game(self) -> Optional[str]:
        """Detect which game is playing by cross-referencing window title with guides"""
        games = self.knowledge.list_games()
        valid_games = [g for g in games if not g.upper().startswith("EXAMPLE")]
        
        if not valid_games:
            return None
        
        # Try to match the emulator window title with a known game
        window_title = self.vision.target_window_title.lower()
        if window_title:
            for game in valid_games:
                # Check if any word from the game name appears in window title
                game_words = game.lower().replace("_", " ").split()
                match_count = sum(1 for w in game_words if w in window_title and len(w) > 2)
                if match_count > 0:
                    print(f"Game matched from window title: {game}")
                    return game
            
            # Also check abbreviation matching (e.g. "MGS2" -> "Metal Gear Solid 2")
            game_abbreviations = {
                "mgs": "metal gear solid",
                "mgs2": "metal gear solid 2",
                "mgs3": "metal gear solid 3",
                "re": "resident evil",
                "re2": "resident evil 2",
                "sh": "silent hill",
                "ff": "final fantasy",
                "dmc": "devil may cry",
                "kh": "kingdom hearts",
            }
            for abbr, full_name in game_abbreviations.items():
                if abbr in window_title or full_name in window_title:
                    for game in valid_games:
                        if abbr == game.lower() or full_name in game.lower():
                            print(f"Game matched from abbreviation: {game}")
                            return game
        
        # Fallback: return first valid game
        if valid_games:
            return valid_games[0]
        
        return None
    
    def _get_session_state(self) -> str:
        """Get current session state for context"""
        summary = self.session.get_session_summary()
        if not summary:
            return "New game session"
        
        lines = []
        if summary.get("current_location"):
            lines.append(f"Location: {summary['current_location']}")
        if summary.get("current_objective"):
            lines.append(f"Objective: {summary['current_objective']}")
        if summary.get("inventory"):
            lines.append(f"Inventory: {', '.join(summary['inventory'][:5])}")
        if summary.get("locations_visited"):
            lines.append(f"Areas visited: {len(summary['locations_visited'])}")
        if summary.get("stuck_areas"):
            lines.append(f"Stuck areas: {', '.join(summary['stuck_areas'][:3])}")
        if summary.get("recent_notes"):
            notes = [n for n in summary["recent_notes"] if n]
            if notes:
                lines.append(f"Player notes: {'; '.join(notes[:3])}")
        
        # Add AI memory context
        ai_memory = self.session.get_ai_memory_context(limit=5)
        if ai_memory:
            lines.append(ai_memory)
        
        return "\n".join(lines) if lines else "Starting game"
    
    def _get_history_text(self) -> str:
        """Get recent analysis history as text"""
        if not self.analysis_history:
            return "No previous observations"
        return "\n".join(f"- {h}" for h in self.analysis_history[-5:])
    
    def _update_history(self, task: str):
        """Update analysis history and detect if player is stuck"""
        self.analysis_history.append(task)
        if len(self.analysis_history) > 10:
            self.analysis_history = self.analysis_history[-10:]
        
        # Detect stuck: if last 3 analyses are very similar
        if len(self.analysis_history) >= 3:
            recent = self.analysis_history[-3:]
            # Check if words overlap significantly
            words_sets = [set(a.lower().split()) for a in recent]
            if len(words_sets[0] & words_sets[1] & words_sets[2]) > 3:
                self.stuck_counter += 1
            else:
                self.stuck_counter = 0
        
    def _analyze_with_ollama(self, frame, game_context: str) -> str:
        """Analyze screenshot with Ollama (local, no limits!)"""
        if not self.ollama_model:
            return "Waiting for task..."
        
        try:
            # Prepare prompt with history
            prompt_template = self.PASSIVE_PROMPT if self.passive_mode else self.ACTIVE_PROMPT
            
            stuck_hint = ""
            if not self.passive_mode and self.stuck_counter >= 2:
                stuck_hint = self.STUCK_HINT
            
            format_args = {
                "game_name": self.current_game or "Unknown Game",
                "session_state": self._get_session_state(),
                "history": self._get_history_text(),
                "game_context": game_context[:2000] if game_context else "No game data loaded",
            }
            
            if not self.passive_mode:
                format_args["stuck_hint"] = stuck_hint
            
            prompt = prompt_template.format(**format_args)
            
            # Convert frame to base64 for vision models
            img = Image.fromarray(frame)
            img.thumbnail((800, 600))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Check if model supports vision
            is_vision_model = any(v in self.ollama_model.lower() for v in ["llava", "bakllava", "moondream"])
            
            if is_vision_model:
                response = ollama.chat(
                    model=self.ollama_model,
                    messages=[{
                        'role': 'user',
                        'content': prompt,
                        'images': [img_base64]
                    }],
                    options={
                        'temperature': 0.3,
                        'num_predict': 50
                    }
                )
            else:
                # Text-only model - use just the prompt with context
                response = ollama.chat(
                    model=self.ollama_model,
                    messages=[{
                        'role': 'user',
                        'content': prompt
                    }],
                    options={
                        'temperature': 0.3,
                        'num_predict': 50
                    }
                )
            
            result = response['message']['content'].strip()
            
            # Clean up response
            for prefix in ["JOURNAL NOTE:", "NEXT ACTION:", "Journal note:", "Next action:"]:
                if result.startswith(prefix):
                    result = result[len(prefix):].strip()
            
            return result
            
        except Exception as e:
            print(f"Ollama error: {e}")
            return "Waiting for task..."
    
    def _analyze_with_gemini(self, frame, game_context: str) -> str:
        """Analyze screenshot with Gemini Vision (cloud, has rate limits)"""
        if not self.gemini_client:
            return "Waiting for task..."
        
        try:
            img = Image.fromarray(frame)
            img.thumbnail((800, 600))
            
            prompt_template = self.PASSIVE_PROMPT if self.passive_mode else self.ACTIVE_PROMPT
            
            stuck_hint = ""
            if not self.passive_mode and self.stuck_counter >= 2:
                stuck_hint = self.STUCK_HINT
            
            format_args = {
                "game_name": self.current_game or "Unknown Game",
                "session_state": self._get_session_state(),
                "history": self._get_history_text(),
                "game_context": game_context[:1500] if game_context else "No game data loaded",
            }
            
            if not self.passive_mode:
                format_args["stuck_hint"] = stuck_hint
            
            prompt = prompt_template.format(**format_args)
            
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=[prompt, img],
                config=types.GenerateContentConfig(
                    max_output_tokens=50,
                    temperature=0.3
                )
            )
            
            result = response.text.strip()
            
            for prefix in ["JOURNAL NOTE:", "NEXT ACTION:", "Journal note:", "Next action:"]:
                if result.startswith(prefix):
                    result = result[len(prefix):].strip()
            
            return result
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print("Rate limit hit - waiting...")
                return None
            print(f"Gemini error: {e}")
            return "Waiting for task..."
    
    def _analyze_frame(self, frame, game_context: str) -> Optional[str]:
        """Analyze frame using the best available LLM"""
        if self.ollama_model:
            return self._analyze_with_ollama(frame, game_context)
        elif self.gemini_client:
            return self._analyze_with_gemini(frame, game_context)
        return "No LLM configured"
    
    def process_frame(self) -> Tuple[Optional[str], Optional[str]]:
        """Process a frame from the screen"""
        frame = self.vision.capture_screen(save_debug=False)
        if frame is None:
            return None, None
        
        # Build smarter search terms based on session state
        search_terms = ["objective", "location", "area", "next step"]
        
        # Add context from current state
        summary = self.session.get_session_summary()
        if summary.get("current_location"):
            search_terms.append(summary["current_location"])
        if summary.get("current_objective"):
            search_terms.append(summary["current_objective"])
        
        # Add terms from recent history
        if self.analysis_history:
            last = self.analysis_history[-1]
            # Extract key words from last analysis
            for word in last.split():
                if len(word) > 4 and word.isalpha():
                    search_terms.append(word)
        
        game_context = ""
        game_filter = self.current_game
        
        seen_content = set()
        for term in search_terms[:6]:  # Limit to 6 searches
            results = self.knowledge.search(term, k=2, game_filter=game_filter)
            for r in results:
                content_key = r["content"][:50]
                if content_key not in seen_content:
                    seen_content.add(content_key)
                    game_context += r["content"] + "\n\n"
        
        # Analyze with LLM
        task = self._analyze_frame(frame, game_context)
        
        # If rate limited, don't update
        if task is None:
            return None, None
        
        # Avoid repeating the exact same task
        if task == self.last_task:
            return None, None
        
        self.last_task = task
        self._update_history(task)
        
        # Save AI observation to session memory
        self.session.add_ai_memory(task, summary.get("current_location"))
        
        if self.stuck_counter >= 2:
            print(f"\nPlayer seems stuck! Giving more specific hints...")
            # Record stuck area
            location = summary.get("current_location", "unknown area")
            if location:
                self.session.add_stuck_area(location)
        
        # Save tips to avoid repetition
        if not self.passive_mode:
            self.session.add_tip(task)
        
        print(f"\nNew note: {task}")
        
        context = None
        if self.current_game:
            context = f"{self.current_game}"
        
        return task, context
    
    def get_update(self) -> Optional[Tuple[str, Optional[str]]]:
        try:
            task, context = self.process_frame()
            if task:
                return task, context
        except Exception as e:
            print(f"Processing error: {e}")
        
        return None
    
    def run_cli(self, interval: float = 15.0):
        print("\nStarting CLI mode...")
        print("   Press Ctrl+C to stop\n")
        
        self.is_running = True
        
        try:
            while self.is_running:
                task, context = self.process_frame()
                
                if task:
                    print(f"\n{'='*50}")
                    print(f"NOTE: {task}")
                    if context:
                        print(f"{context}")
                    print(f"{'='*50}\n")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\nXayk Noob's Journal stopped!")
            self.is_running = False
    
    def run_overlay(self, interval_ms: int = 10000, mode: str = "guide"):
        """Run with overlay - guide mode (tells what to do)"""
        print(f"\nStarting Overlay mode ({mode})...")
        
        if mode == "journal":
            return self.run_journal(interval_ms)
        
        # Guide mode - original overlay
        app = RetroTaskerApp()
        app.set_update_callback(self.get_update)
        app.start_monitoring(interval_ms=interval_ms)
        
        # Show recap if returning player
        if self.session.current_session and self.session.current_session.get("play_count", 1) > 1:
            recap = self.session.get_recap()
            app.overlay.set_task(recap.split('\n')[0], self.current_game)
        else:
            app.overlay.set_task("Waiting for task...", self.current_game)
        
        result = app.run()
        
        # Save session summary on exit
        self.session.end_session_summary()
        print("Session saved!")
        
        return result
    
    def run_journal(self, interval_ms: int = 10000):
        """Run with journal overlay - manual notes only, no AI auto-notes"""
        print("\nStarting Journal mode...")
        
        app = JournalApp()
        
        # Load existing session data
        if self.session.current_session:
            for item in self.session.current_session.get("items_found", []):
                app.overlay.add_item(item["name"], "item")
            for loc in self.session.current_session.get("locations_visited", []):
                app.overlay.add_location(loc["name"])
            for obj in self.session.current_session.get("objectives_completed", []):
                app.overlay.add_objective(obj["description"], checked=True)
            for note in self.session.get_notes():
                note_type = note.get("type", "note")
                note_text = note.get("text", "")
                timestamp = note.get("created_at", "")
                if note_text:
                    app.overlay.add_item(note_text, note_type)
        
        # Connect item checks to session manager
        def on_item_checked(text, item_type, checked):
            if checked and item_type == "item":
                self.session.use_item(text)
            elif checked and item_type == "objective":
                self.session.complete_objective(text)
        
        # Save notes when added
        def on_note_added(text, note_type):
            self.session.add_note(text, note_type)
            print(f"Saved: [{note_type}] {text}")
        
        # Delete notes when removed
        def on_note_deleted(text, note_type):
            self.session.delete_note(text, note_type)
            print(f"Deleted: [{note_type}] {text}")
        
        app.overlay.item_checked.connect(on_item_checked)
        app.overlay.note_added.connect(on_note_added)
        app.overlay.note_deleted.connect(on_note_deleted)
        
        # Journal is manual-only: no AI auto-tracking
        if self.current_game:
            app.overlay.set_current_task(f"Playing: {self.current_game}")
        else:
            app.overlay.set_current_task("Add your notes below")
        
        app.overlay.set_status("READY", True)
        
        result = app.run()
        
        # Save session summary on exit
        self.session.end_session_summary()
        print("Session saved!")
        
        return result
    
    def get_journal_update(self) -> Optional[Tuple[str, str]]:
        """Get update for journal mode - returns detected items/locations"""
        try:
            task, context = self.process_frame()
            if task and task != "Waiting for task...":
                # Parse task to detect items or locations
                task_lower = task.lower()
                
                # Detect items
                item_keywords = ["found", "picked up", "got", "acquired", "item"]
                if any(kw in task_lower for kw in item_keywords):
                    return ("item", task)
                
                # Detect locations
                loc_keywords = ["entered", "arrived", "reached", "location", "area", "room"]
                if any(kw in task_lower for kw in loc_keywords):
                    # Update session
                    self.session.visit_location(task)
                    return ("location", task)
                
                # Default: just update current task display
                return ("task", task)
        except Exception as e:
            print(f"Journal update error: {e}")
        
        return None


def create_env_template():
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# Xayk Noob's Journal - Configuration

# LLM Provider: "auto", "ollama", or "gemini"
# auto = tries Ollama first (local, no limits), then Gemini
LLM_PROVIDER=auto

# For Gemini (optional, has rate limits)
# Get your key at: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Mode: "passive" (no spoilers) or "active" (with hints)
MODE=passive
"""
        try:
            env_file.write_text(env_content)
            print("Created .env file! Configure your settings.")
            return True
        except PermissionError:
            print("Warning: Could not create .env file (permission denied)")
            print("You can manually create it or check file permissions")
            return False
    return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Xayk Noob's Journal - Retro game assistant with AI vision"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["overlay", "cli", "test", "reindex", "config", "launcher"],
        default="launcher",
        help="Execution mode (default: launcher)"
    )
    parser.add_argument(
        "--ui-mode",
        choices=["journal", "guide"],
        default=None,
        help="UI mode: journal (checkboxes) or guide (instructions)"
    )
    parser.add_argument(
        "--game", "-g",
        type=str,
        default=None,
        help="Game name (folder in guides/)"
    )
    parser.add_argument(
        "--emulator", "-e",
        type=str,
        default=None,
        help="Emulator window title"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=10000,
        help="Update interval in ms (default: 10000 - 10 seconds)"
    )
    parser.add_argument(
        "--llm",
        choices=["auto", "ollama", "gemini"],
        default="auto",
        help="LLM provider (default: auto)"
    )
    parser.add_argument(
        "--no-launcher",
        action="store_true",
        default=False,
        help="Skip launcher and start directly"
    )
    
    args = parser.parse_args()
    
    # Config mode
    if args.mode == "config":
        from config_dialog import ConfigDialog
        from PyQt6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        dialog = ConfigDialog()
        dialog.exec()
        return 0
    
    create_env_template()
    
    # Reindex mode
    if args.mode == "reindex":
        print("\nReindexing knowledge base...")
        kb = KnowledgeBase()
        kb.reindex()
        print("Done!")
        return 0
    
    # Test mode
    if args.mode == "test":
        print("\nTest mode - checking components...\n")
        
        print("[Vision Engine]")
        from vision_engine import main as vision_test
        vision_test()
        
        print("\n[Knowledge Base]")
        from knowledge_base import main as kb_test
        kb_test()
        
        print("\n[Session Manager]")
        from session_manager import main as session_test
        session_test()
        
        print("\nTests completed!")
        return 0
    
    # Launcher mode (default) - show game/mode selection
    selected_game = args.game
    selected_mode = args.ui_mode or "journal"
    
    if args.mode == "launcher" and not args.no_launcher:
        try:
            from launcher import run_launcher
            selected_game, selected_mode = run_launcher()
            
            if selected_mode is None:
                print("Launcher cancelled.")
                return 0
        except ImportError:
            print("Launcher not available, using defaults...")
    
    # Get LLM provider from env or args
    llm_provider = os.getenv("LLM_PROVIDER", args.llm)
    
    # Determine passive mode based on UI mode
    passive_mode = selected_mode == "journal"
    
    print(f"\nStarting with:")
    print(f"  Game: {selected_game or 'Auto-detect'}")
    print(f"  Mode: {selected_mode}")
    print(f"  LLM: {llm_provider}")
    
    # Create tasker
    tasker = RetroTasker(
        emulator_title=args.emulator,
        llm_provider=llm_provider,
        passive_mode=passive_mode
    )
    
    # Override game if selected
    if selected_game:
        tasker.current_game = selected_game
        tasker.session.start_session(selected_game)
    
    # Run in selected mode
    if args.mode == "cli":
        tasker.run_cli(interval=args.interval / 1000)
        return 0
    else:
        return tasker.run_overlay(interval_ms=args.interval, mode=selected_mode)


if __name__ == "__main__":
    sys.exit(main())
