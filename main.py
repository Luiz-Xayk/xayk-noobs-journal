import os
import sys
import time
import base64
import io
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

from vision_engine import VisionEngine
from knowledge_base import KnowledgeBase
from overlay_ui import RetroTaskerApp

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class RetroTasker:
    
    # Prompt para análise visual do jogo
    VISION_PROMPT = """You are a retro game assistant analyzing a screenshot from {game_name}.

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
- If unclear, say "Explore the area" or similar
- Answer in English

NEXT ACTION:"""

    def __init__(self, 
                 emulator_title: Optional[str] = None):
        print("=" * 60)
        print("XAYK NOOB'S JOURNAL - Initializing...")
        print("=" * 60)
        
        print("\n[1/4] Starting Vision Engine...")
        self.vision = VisionEngine()
        
        print("\n[2/4] Starting Knowledge Base...")
        self.knowledge = KnowledgeBase()
        
        print("\n[3/4] Configuring Gemini Vision...")
        self._setup_gemini()
        
        print("\n[4/4] Searching for emulator window...")
        if emulator_title:
            self.vision.find_emulator_window(emulator_title)
        else:
            self.vision.find_emulator_window()
        
        self.last_task = ""
        self.is_running = False
        self.current_game = self._detect_game()
        
        print("\n" + "=" * 60)
        print("Xayk Noob's Journal ready!")
        if self.current_game:
            print(f"Game detected: {self.current_game}")
        print("=" * 60)
    
    def _setup_gemini(self):
        self.gemini_client = None
        self.gemini_model = None
        
        if not GEMINI_AVAILABLE:
            print("Gemini not available. Install with: pip install google-genai")
            return
        
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("GEMINI_API_KEY not found in .env")
            return
        
        try:
            self.gemini_client = genai.Client(api_key=api_key)
            self.gemini_model = "gemini-2.0-flash"
            print("Gemini Vision configured!")
        except Exception as e:
            print(f"Error configuring Gemini: {e}")
    
    def _detect_game(self) -> Optional[str]:
        """Detecta qual jogo está carregado na knowledge base"""
        games = self.knowledge.list_games()
        if games:
            # Procura por GameData primeiro
            for game in games:
                if "GameData" in game:
                    return game.replace("_GameData", "").replace("_", " ")
            return games[0]
        return None
    
    def _image_to_base64(self, frame) -> str:
        """Converte frame numpy para base64"""
        img = Image.fromarray(frame)
        # Reduz tamanho para economizar tokens
        img.thumbnail((800, 600))
        
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode()
    
    def _analyze_with_vision(self, frame, game_context: str) -> str:
        """Analisa a screenshot com Gemini Vision"""
        if not self.gemini_client:
            return "Waiting for task..."
        
        try:
            # Converte frame para PIL Image
            img = Image.fromarray(frame)
            img.thumbnail((800, 600))  # Reduz tamanho para economizar tokens
            
            # Prepara o prompt (mais curto para economizar tokens)
            prompt = self.VISION_PROMPT.format(
                game_name=self.current_game or "Unknown Game",
                game_context=game_context[:1500] if game_context else "No game data loaded"
            )
            
            # Envia para Gemini Vision
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=[
                    prompt,
                    img
                ],
                config=types.GenerateContentConfig(
                    max_output_tokens=50,
                    temperature=0.3
                )
            )
            
            result = response.text.strip()
            # Remove prefixos comuns
            for prefix in ["NEXT ACTION:", "Next action:", "Action:"]:
                if result.startswith(prefix):
                    result = result[len(prefix):].strip()
            
            return result
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print("Rate limit hit - waiting...")
                return None  # Retorna None para não atualizar a task
            print(f"Vision analysis error: {e}")
            return "Waiting for task..."
    
    def process_frame(self) -> Tuple[Optional[str], Optional[str]]:
        """Processa um frame da tela"""
        frame = self.vision.capture_screen(save_debug=False)
        if frame is None:
            return None, None
        
        # Busca contexto do jogo na knowledge base
        # Usa termos genéricos para buscar áreas do jogo
        search_terms = ["objective", "location", "area", "next step"]
        game_context = ""
        
        for term in search_terms:
            context = self.knowledge.search_context(term, k=3)
            if context:
                game_context += context + "\n"
        
        # Analisa com Gemini Vision
        task = self._analyze_with_vision(frame, game_context)
        
        # Se retornou None (rate limit), não atualiza
        if task is None:
            return None, None
        
        # Evita repetir a mesma task
        if task == self.last_task:
            return None, None
        
        self.last_task = task
        print(f"\nNew task: {task}")
        
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
                    print(f"TASK: {task}")
                    if context:
                        print(f"{context}")
                    print(f"{'='*50}\n")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\nXayk Noob's Journal stopped!")
            self.is_running = False
    
    def run_overlay(self, interval_ms: int = 5000):
        print("\nStarting Overlay mode...")
        
        app = RetroTaskerApp()
        app.set_update_callback(self.get_update)
        app.start_monitoring(interval_ms=interval_ms)
        
        # Mensagem inicial
        app.overlay.set_task("Waiting for task...", self.current_game)
        
        return app.run()


def create_env_template():
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# Xayk Noob's Journal - Configuration

# Google Gemini API Key (required for vision analysis)
# Get your key at: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here
"""
        env_file.write_text(env_content)
        print("Created .env file! Configure your API key.")
        return True
    return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Xayk Noob's Journal - Retro game assistant with AI vision"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["overlay", "cli", "test", "reindex"],
        default="overlay",
        help="Execution mode (default: overlay)"
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
        default=15000,
        help="Update interval in ms (default: 15000 - 15 seconds)"
    )
    
    args = parser.parse_args()
    
    create_env_template()
    
    if args.mode == "reindex":
        print("\nReindexing knowledge base...")
        kb = KnowledgeBase()
        kb.index_guides(force_reindex=True)
        print("Done!")
        return 0
    
    if args.mode == "test":
        print("\nTest mode - checking components...\n")
        
        print("[Vision Engine]")
        from vision_engine import main as vision_test
        vision_test()
        
        print("\n[Knowledge Base]")
        from knowledge_base import main as kb_test
        kb_test()
        
        print("\nTests completed!")
        return 0
    
    tasker = RetroTasker(
        emulator_title=args.emulator
    )
    
    if args.mode == "overlay":
        return tasker.run_overlay(interval_ms=args.interval)
    elif args.mode == "cli":
        tasker.run_cli(interval=args.interval / 1000)
        return 0


if __name__ == "__main__":
    sys.exit(main())
