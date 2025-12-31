# services/session_store.py
import os
import json
import uuid
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from .storage import UPLOAD_DIR

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
#full_path = os.path.join(UPLOAD_DIR, filename)

# Ensure folders exist
os.makedirs(SESSIONS_DIR, exist_ok=True)

class SessionStore:
    """
    In-memory session store with optional on-disk JSON snapshots in data/sessions/{id}.json
    Structure:
    {
      session_id: {
        "created_at": ISO8601,
        "chat_history": [ {"role":"user","text":"..."}, {"role":"assistant","text":"..."} ],
        "image_history": [ {"filename":"...", "analysis": {...}} ]
      }
    }
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: Dict[str, Dict[str, Any]] = {}

    # ---- basic helpers ----
    def _path(self, session_id: str) -> str:
        return os.path.join(SESSIONS_DIR, f"{session_id}.json")

    def _save_snapshot(self, session_id: str) -> None:
        path = self._path(session_id)
        with self._lock:
            data = self._sessions.get(session_id)
            if data is None:
                return
            with open(path, "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=2, ensure_ascii=False)

    # ---- API ----
    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        with self._lock:
            self._sessions[session_id] = {
                "created_at": datetime.utcnow().isoformat() + "Z",
                "chat_history": [],
                "image_history": [],
            }
        self._save_snapshot(session_id)
        return session_id

    def create_session_with_id(self, session_id: str) -> str:
        """
        Create a session using a specific session_id.
        If session already exists, do nothing.
        """
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = {
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "chat_history": [],
                    "image_history": [],
                }
        self._save_snapshot(session_id)
        return session_id
    
    
    # services/session_store.py (Inside class SessionStore:)

    # ... (after def add_image_analysis)

    def add_chat_message(self, session_id: str, user_msg: Dict[str, str], bot_msg: Dict[str, str]) -> None:
        """
        Adds a single user message and a single bot response (like analysis results)
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError("Invalid session_id")
            
            # The structure is assumed to be {"role": ..., "text": ...}
            # We add both objects to the history array
            self._sessions[session_id]["chat_history"].append(user_msg)
            self._sessions[session_id]["chat_history"].append(bot_msg)

        self._save_snapshot(session_id)

    def exists(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._sessions

    def add_chat(self, session_id: str, role: str, text: str) -> None:
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError("Invalid session_id")
            # Normalize role to match OpenAI API requirements
        role_map = {
            "bot": "assistant",
            "ai": "assistant",
            "human": "user"
        }
        normalized_role = role_map.get(role, role)  # fallback to same if already valid

        self._sessions[session_id]["chat_history"].append({
            "role": normalized_role,
            "text": text
        })

        self._save_snapshot(session_id)

    def add_image_analysis(self, session_id: str, filename: str, analysis: Dict[str, Any]) -> None:
        
        image_full_path = os.path.join(UPLOAD_DIR, filename) 

        with self._lock:
            if session_id not in self._sessions:
                raise KeyError("Invalid session_id")
            self._sessions[session_id]["image_history"].append({
                "filename": filename,
                "image_path": image_full_path, # <--- CORRECTED
                "analysis": analysis
            })
        self._save_snapshot(session_id)

    def get_history(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            return self._sessions.get(session_id, {})

    def end_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Pop and return the final session content. Also keeps a final snapshot file."""
        with self._lock:
            data = self._sessions.pop(session_id, None)
        if data is None:
            return None
        # Keep a final, immutable snapshot on disk for later viewing
        final_path = self._path(session_id)
        with open(final_path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2, ensure_ascii=False)
        return data