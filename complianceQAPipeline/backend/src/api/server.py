import uuid
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware 
from fastapi import UploadFile, File
import os
from pydantic import BaseModel
from typing import List,Optional

from dotenv import load_dotenv
load_dotenv(override=True)

from backend.src.api.telemetry import setup_telemetry
setup_telemetry()

from backend.src.graph.workflow import app as compliance_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-server")

app = FastAPI(
    title="Brand Gaurdian AI API",
    description= "API for auditing video content against the brand compliance rules.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",   # local streamlit
        "http://127.0.0.1:8501",
        "*"  # allow all (safe for demo/student project)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# class AuditRequest(BaseModel):
#     '''
#     Define the expected structure of incoming API requests
#     Example valid request:
#         {
#             "video_url":"https://youtu.be/xTpv9lc_qMw",
#         }
#     '''
#     video_url : str
    
class ComplianceIssue(BaseModel):
    category: str
    severity: str
    description: str
    
class AuditResponse(BaseModel):
    session_id: str
    video_id: str
    status: str
    final_report: str
    compliance_results : List[ComplianceIssue]
    
    
    
@app.post("/audit", response_model=AuditResponse)
async def audit_video(file: UploadFile = File(...)):

    session_id = str(uuid.uuid4())
    video_id_short = f"vid_{session_id[:8]}"

    logger.info(f"Received audit file: {file.filename} (Session: {session_id})")

    temp_file_path = f"temp_{video_id_short}_{file.filename}"

    try:
        # Save uploaded file temporarily
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await file.read())

        initial_inputs = {
            "video_path": temp_file_path,
            "video_id": video_id_short,
            "compliance_results": [],
            "errors": []
        }

        final_state = compliance_graph.invoke(initial_inputs)

        return AuditResponse(
            session_id=session_id,
            video_id=final_state.get("video_id"),
            status=final_state.get("final_status", "UNKNOWN"),
            final_report=final_state.get("final_report", "No Report Generated."),
            compliance_results=final_state.get("compliance_results", [])
        )

    except Exception as e:
        logger.error(f"Audit Failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow Execution Failed: {str(e)}"
        )

    finally:
        # 🔥 Always delete local temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
@app.get("/health")
def health_check():
    '''
    Endpoint to verify API working or not!
    '''
    return {"status":"Healthy", "service":"Brand Guardian AI"}