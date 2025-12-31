from fastapi import APIRouter, HTTPException 
from fastapi.responses import FileResponse, StreamingResponse 
import os, io, zipfile 
from services.storage import REPORT_DIR, list_reports as storage_list_reports 

router = APIRouter(prefix="/reports", tags=["Reports"]) 
@router.get("/list/", name="Get Reports List") 


def reports_list(): 
    """Return the registry (data/reports.json).""" 
    return storage_list_reports() 

@router.get("/download/{report_id}/") 

def download_report(report_id: str): 
    reports = storage_list_reports() 
    
    # Find the report by id 
    report = next((r for r in reports if r["id"] == report_id), None) 
    if not report: 
        raise HTTPException(status_code=404, detail="Report not found") 
    file_path = report.get("path") or os.path.join(REPORT_DIR, report["filename"]) 
    if not os.path.exists(file_path): 
        raise HTTPException(status_code=404, detail="File not found") 
    return FileResponse( file_path, media_type="application/pdf", filename=report["filename"], )