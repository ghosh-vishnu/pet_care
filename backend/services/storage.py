import json 
import os 
from datetime import datetime 
from typing import Any, Dict, List 
BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 
DATA_DIR = os.path.join(BASE_DIR, "data") 
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_images") 
REPORT_DIR = os.path.join(DATA_DIR, "reports") 
HISTORY_FILE = os.path.join(DATA_DIR, "history.json") 
IMAGES_FILE = os.path.join(DATA_DIR, "images.json") 
REPORTS_FILE = os.path.join(DATA_DIR, "reports.json") 
def ensure_dirs(): 
    os.makedirs(DATA_DIR, exist_ok=True) 
    os.makedirs(UPLOAD_DIR, exist_ok=True) 
    os.makedirs(REPORT_DIR, exist_ok=True) 
    for f in [HISTORY_FILE, IMAGES_FILE, REPORTS_FILE]: 
        if not os.path.exists(f): 
            with open(f, "w", encoding="utf-8") as fp: 
                json.dump([], fp) 
# --- Base JSON helpers --- 
def _load(path: str) -> List[Dict[str, Any]]: 
    with open(path, "r", encoding="utf-8") as fp: 
        return json.load(fp) 
def _save(path: str, data: List[Dict[str, Any]]) -> None: 
    with open(path, "w", encoding="utf-8") as fp: 
        json.dump(data, fp, indent=2, ensure_ascii=False) 


# --- Safer JSON helpers (with default) --- 

def _load_json(path: str, default): 
    if not os.path.exists(path): 
        return default 
    try: 
        with open(path, "r", encoding="utf-8") as fp: return json.load(fp) 
    
    except Exception: 
        return default 
def _save_json(path: str, data): 
    with open(path, "w", encoding="utf-8") as fp: 
        json.dump(data, fp, indent=2, ensure_ascii=False) 
        
# --- Chat history --- 

def add_chat(question: str, answer: str, matched: str, score: float) -> Dict[str, Any]: 
    hist = _load(HISTORY_FILE) 
    item = { 
            "id": f"chat_{len(hist)+1}", "ts": datetime.utcnow().isoformat() + "Z", "question": question, "answer": answer, "matched_question": matched, "score": score } 
    hist.append(item) 
    _save(HISTORY_FILE, hist) 
    return item 

def get_history(n: int = 50) -> List[Dict[str, Any]]: 
    hist = _load(HISTORY_FILE) 
    return hist[-n:] 

# --- Images --- 


def register_image(filename: str, path: str) -> Dict[str, Any]: 
    imgs = _load(IMAGES_FILE) 
    item = { 
            "id": f"img_{len(imgs)+1}", "filename": filename, "path": path, "ts": datetime.utcnow().isoformat() + "Z" } 
    imgs.append(item) 
    _save(IMAGES_FILE, imgs) 
    return item 

def get_image(image_id: str) -> Dict[str, Any]: 
    imgs = _load(IMAGES_FILE) 
    for i in imgs: 
        if i["id"] == image_id: 
            return i 
    raise KeyError("image not found") 

# --- Reports --- 


def register_report(filename: str) -> Dict[str, Any]: 
    reports = _load_json(REPORTS_FILE, []) 
    new_id = f"rep_{len(reports)+1}" 
    # prevent duplicates 
    for r in reports: 
        if r["filename"] == filename: 
            return r 
    entry = { 
             "id": new_id, "filename": filename, "path": os.path.join(REPORT_DIR, filename), "ts": datetime.utcnow().isoformat() + "Z", } 
    reports.append(entry) 
    _save_json(REPORTS_FILE, reports) 
    return entry 

def list_reports() -> List[Dict[str, Any]]: 
    return _load_json(REPORTS_FILE, [])