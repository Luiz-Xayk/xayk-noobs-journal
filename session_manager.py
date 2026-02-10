import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any


class SessionManager:
    """
    Manages game session persistence - "Save State with Memory"
    Tracks items found, locations visited, and objectives completed.
    """
    
    def __init__(self, sessions_folder: str = "sessions"):
        self.sessions_folder = Path(sessions_folder)
        self.sessions_folder.mkdir(exist_ok=True)
        
        self.current_session: Optional[Dict] = None
        self.current_game: Optional[str] = None
        self.session_file: Optional[Path] = None
    
    def start_session(self, game_name: str) -> Dict:
        """Start or resume a session for a game"""
        self.current_game = game_name
        safe_name = game_name.replace(" ", "_").replace(":", "").lower()
        self.session_file = self.sessions_folder / f"{safe_name}_session.json"
        
        if self.session_file.exists():
            self.current_session = self._load_session()
            self.current_session["last_played"] = datetime.now().isoformat()
            self.current_session["play_count"] = self.current_session.get("play_count", 0) + 1
            print(f"Resumed session for {game_name}")
        else:
            self.current_session = self._create_new_session(game_name)
            print(f"New session started for {game_name}")
        
        self._save_session()
        return self.current_session
    
    def _create_new_session(self, game_name: str) -> Dict:
        """Create a new empty session"""
        return {
            "game": game_name,
            "created_at": datetime.now().isoformat(),
            "last_played": datetime.now().isoformat(),
            "play_count": 1,
            "total_playtime_minutes": 0,
            "items_found": [],
            "items_used": [],
            "locations_visited": [],
            "current_location": None,
            "objectives_completed": [],
            "current_objective": None,
            "notes": [],
            "events_log": [],
            "ai_memory": [],       # AI observations between sessions
            "stuck_areas": [],     # Areas where player got stuck
            "tips_given": [],      # Tips that were given to avoid repetition
            "session_history": []  # Summary of each play session
        }
    
    def _load_session(self) -> Dict:
        """Load existing session from file"""
        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading session: {e}")
            return self._create_new_session(self.current_game)
    
    def _save_session(self):
        """Save current session to file"""
        if not self.current_session or not self.session_file:
            return
        
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_session, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving session: {e}")
    
    def add_item(self, item_name: str, location: Optional[str] = None):
        """Record that player found an item"""
        if not self.current_session:
            return
        
        item_entry = {
            "name": item_name,
            "found_at": datetime.now().isoformat(),
            "location": location
        }
        
        existing_items = [i["name"].lower() for i in self.current_session["items_found"]]
        if item_name.lower() not in existing_items:
            self.current_session["items_found"].append(item_entry)
            self._log_event("ITEM_FOUND", f"Found: {item_name}", location)
            self._save_session()
    
    def use_item(self, item_name: str, purpose: Optional[str] = None):
        """Record that player used an item"""
        if not self.current_session:
            return
        
        use_entry = {
            "name": item_name,
            "used_at": datetime.now().isoformat(),
            "purpose": purpose
        }
        
        self.current_session["items_used"].append(use_entry)
        self._log_event("ITEM_USED", f"Used: {item_name}", purpose)
        self._save_session()
    
    def visit_location(self, location_name: str):
        """Record that player visited a location"""
        if not self.current_session:
            return
        
        existing = [loc["name"].lower() for loc in self.current_session["locations_visited"]]
        if location_name.lower() not in existing:
            location_entry = {
                "name": location_name,
                "first_visited": datetime.now().isoformat()
            }
            self.current_session["locations_visited"].append(location_entry)
            self._log_event("LOCATION_VISITED", f"Visited: {location_name}")
        
        self.current_session["current_location"] = location_name
        self._save_session()
    
    def complete_objective(self, objective: str):
        """Record that player completed an objective"""
        if not self.current_session:
            return
        
        obj_entry = {
            "description": objective,
            "completed_at": datetime.now().isoformat()
        }
        
        self.current_session["objectives_completed"].append(obj_entry)
        self._log_event("OBJECTIVE_COMPLETED", objective)
        self._save_session()
    
    def set_current_objective(self, objective: str):
        """Set the current objective"""
        if not self.current_session:
            return
        
        self.current_session["current_objective"] = objective
        self._save_session()
    
    def add_note(self, note: str, note_type: str = "note"):
        """Add a manual note to the session"""
        if not self.current_session:
            return
        
        note_entry = {
            "text": note,
            "type": note_type,
            "created_at": datetime.now().isoformat()
        }
        
        # Avoid duplicates
        existing = [n["text"].lower() for n in self.current_session["notes"]]
        if note.lower() not in existing:
            self.current_session["notes"].append(note_entry)
            self._save_session()
    
    def delete_note(self, note_text: str, note_type: str = "note"):
        """Delete a note from the session"""
        if not self.current_session:
            return
        
        self.current_session["notes"] = [
            n for n in self.current_session["notes"]
            if not (n["text"].lower() == note_text.lower() and n.get("type", "note") == note_type)
        ]
        self._save_session()
    
    def get_notes(self) -> List[Dict]:
        """Get all notes from the current session"""
        if not self.current_session:
            return []
        return self.current_session.get("notes", [])
    
    def add_ai_memory(self, observation: str, location: Optional[str] = None):
        """Store an AI observation for cross-session memory"""
        if not self.current_session:
            return
        
        if "ai_memory" not in self.current_session:
            self.current_session["ai_memory"] = []
        
        memory_entry = {
            "observation": observation,
            "location": location,
            "timestamp": datetime.now().isoformat()
        }
        
        # Avoid duplicate memories
        existing = [m["observation"].lower() for m in self.current_session["ai_memory"]]
        if observation.lower() not in existing:
            self.current_session["ai_memory"].append(memory_entry)
            # Keep last 50 memories
            if len(self.current_session["ai_memory"]) > 50:
                self.current_session["ai_memory"] = self.current_session["ai_memory"][-50:]
            self._save_session()
    
    def add_stuck_area(self, area: str, attempts: int = 1):
        """Record an area where the player got stuck"""
        if not self.current_session:
            return
        
        if "stuck_areas" not in self.current_session:
            self.current_session["stuck_areas"] = []
        
        # Check if already recorded
        for stuck in self.current_session["stuck_areas"]:
            if stuck["area"].lower() == area.lower():
                stuck["attempts"] = stuck.get("attempts", 1) + attempts
                stuck["last_stuck"] = datetime.now().isoformat()
                self._save_session()
                return
        
        self.current_session["stuck_areas"].append({
            "area": area,
            "attempts": attempts,
            "first_stuck": datetime.now().isoformat(),
            "last_stuck": datetime.now().isoformat()
        })
        self._save_session()
    
    def add_tip(self, tip: str):
        """Record a tip that was given to avoid repeating it"""
        if not self.current_session:
            return
        
        if "tips_given" not in self.current_session:
            self.current_session["tips_given"] = []
        
        existing = [t.lower() for t in self.current_session["tips_given"]]
        if tip.lower() not in existing:
            self.current_session["tips_given"].append(tip)
            # Keep last 30 tips
            if len(self.current_session["tips_given"]) > 30:
                self.current_session["tips_given"] = self.current_session["tips_given"][-30:]
            self._save_session()
    
    def end_session_summary(self):
        """Save a summary when the session ends"""
        if not self.current_session:
            return
        
        if "session_history" not in self.current_session:
            self.current_session["session_history"] = []
        
        summary = {
            "date": datetime.now().isoformat(),
            "location": self.current_session.get("current_location"),
            "objective": self.current_session.get("current_objective"),
            "items_this_session": len(self.current_session.get("items_found", [])),
            "locations_this_session": len(self.current_session.get("locations_visited", [])),
            "objectives_this_session": len(self.current_session.get("objectives_completed", []))
        }
        
        self.current_session["session_history"].append(summary)
        self._save_session()
    
    def get_ai_memory_context(self, limit: int = 10) -> str:
        """Get AI memory as context text for prompts"""
        if not self.current_session:
            return ""
        
        memories = self.current_session.get("ai_memory", [])[-limit:]
        if not memories:
            return ""
        
        lines = ["Previous observations:"]
        for m in memories:
            loc = f" (at {m['location']})" if m.get('location') else ""
            lines.append(f"- {m['observation']}{loc}")
        
        return "\n".join(lines)
    
    def get_stuck_areas_context(self) -> str:
        """Get stuck areas as context for smarter hints"""
        if not self.current_session:
            return ""
        
        stuck = self.current_session.get("stuck_areas", [])
        if not stuck:
            return ""
        
        lines = ["Areas where player struggled:"]
        for s in stuck:
            lines.append(f"- {s['area']} (stuck {s.get('attempts', 1)} times)")
        
        return "\n".join(lines)
    
    def _log_event(self, event_type: str, description: str, extra: Optional[str] = None):
        """Log an event to the session history"""
        if not self.current_session:
            return
        
        event = {
            "type": event_type,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        if extra:
            event["extra"] = extra
        
        self.current_session["events_log"].append(event)
        
        if len(self.current_session["events_log"]) > 500:
            self.current_session["events_log"] = self.current_session["events_log"][-500:]
    
    def get_recap(self) -> str:
        """Generate a rich recap for when player returns"""
        if not self.current_session:
            return "No active session"
        
        s = self.current_session
        lines = []
        
        lines.append(f"=== Welcome back to {s['game']}! ===")
        lines.append(f"Play session #{s['play_count']}")
        
        if s.get("current_location"):
            lines.append(f"Last location: {s['current_location']}")
        
        if s.get("current_objective"):
            lines.append(f"Current objective: {s['current_objective']}")
        
        # Items
        items_count = len(s.get("items_found", []))
        if items_count > 0:
            lines.append(f"\nItems collected: {items_count}")
            recent_items = s["items_found"][-3:]
            for item in recent_items:
                lines.append(f"  - {item['name']}")
        
        # Locations
        locations_count = len(s.get("locations_visited", []))
        if locations_count > 0:
            lines.append(f"Locations discovered: {locations_count}")
        
        # Objectives
        objectives_count = len(s.get("objectives_completed", []))
        if objectives_count > 0:
            lines.append(f"Objectives completed: {objectives_count}")
        
        # Player notes
        notes = s.get("notes", [])
        if notes:
            recent_notes = notes[-3:]
            lines.append(f"\nRecent notes:")
            for n in recent_notes:
                text = n.get("text", "") if isinstance(n, dict) else str(n)
                lines.append(f"  - {text}")
        
        # Stuck areas warning
        stuck = s.get("stuck_areas", [])
        if stuck:
            lines.append(f"\nDifficult areas:")
            for sa in stuck[-2:]:
                lines.append(f"  ! {sa['area']} (stuck {sa.get('attempts', 1)}x)")
        
        # Last session summary
        history = s.get("session_history", [])
        if history:
            last = history[-1]
            lines.append(f"\nLast session ended at: {last.get('location', 'unknown')}")
        
        return "\n".join(lines)
    
    def has_item(self, item_name: str) -> bool:
        """Check if player has found a specific item"""
        if not self.current_session:
            return False
        
        existing = [i["name"].lower() for i in self.current_session["items_found"]]
        return item_name.lower() in existing
    
    def has_used_item(self, item_name: str) -> bool:
        """Check if player has used a specific item"""
        if not self.current_session:
            return False
        
        used = [i["name"].lower() for i in self.current_session["items_used"]]
        return item_name.lower() in used
    
    def has_visited(self, location_name: str) -> bool:
        """Check if player has visited a location"""
        if not self.current_session:
            return False
        
        visited = [loc["name"].lower() for loc in self.current_session["locations_visited"]]
        return location_name.lower() in visited
    
    def get_inventory(self) -> List[str]:
        """Get list of items found but not used"""
        if not self.current_session:
            return []
        
        found = {i["name"].lower(): i["name"] for i in self.current_session["items_found"]}
        used = {i["name"].lower() for i in self.current_session["items_used"]}
        
        return [found[key] for key in found if key not in used]
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session for AI context"""
        if not self.current_session:
            return {}
        
        s = self.current_session
        return {
            "game": s["game"],
            "current_location": s.get("current_location"),
            "current_objective": s.get("current_objective"),
            "inventory": self.get_inventory(),
            "items_used": [i["name"] for i in s.get("items_used", [])],
            "locations_visited": [loc["name"] for loc in s.get("locations_visited", [])],
            "objectives_completed": [obj["description"] for obj in s.get("objectives_completed", [])],
            "play_count": s.get("play_count", 1),
            "stuck_areas": [sa["area"] for sa in s.get("stuck_areas", [])],
            "recent_notes": [n.get("text", "") for n in s.get("notes", [])[-5:]],
        }
    
    def list_sessions(self) -> List[Dict]:
        """List all saved sessions"""
        sessions = []
        for session_file in self.sessions_folder.glob("*_session.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sessions.append({
                        "game": data.get("game"),
                        "last_played": data.get("last_played"),
                        "play_count": data.get("play_count", 1),
                        "file": str(session_file)
                    })
            except:
                pass
        return sessions


def main():
    print("=" * 50)
    print("Session Manager Test")
    print("=" * 50)
    
    sm = SessionManager()
    
    session = sm.start_session("Metal Gear Solid 2")
    print(f"\nSession started: {session['game']}")
    
    sm.visit_location("Tanker - Deck A")
    sm.add_item("M9 Tranquilizer", "Tanker - Deck A")
    sm.add_item("Ration", "Tanker - Deck A")
    sm.visit_location("Tanker - Deck B")
    sm.set_current_objective("Find the Marines")
    
    print("\nSession Summary:")
    summary = sm.get_session_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\nRecap:")
    print(sm.get_recap())
    
    print("\n" + "=" * 50)
    print("Test completed!")


if __name__ == "__main__":
    main()
