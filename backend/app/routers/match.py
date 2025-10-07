from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ..services.extract import extract_text_from_upload
from ..services.ai_client import generate_jd, ai_match_resumes, generate_interview_email, generate_rejection_email
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["match"])

class GenerateJDRequest(BaseModel):
    job_title: str
    years_experience: int
    must_have_skills: str
    company_name: str
    employment_type: str
    industry: str
    location: str

class EmailData(BaseModel):
    subject: str
    body: str

class CandidateResult(BaseModel):
    filename: str
    score: float
    missing_skills: List[str]
    remarks: str
    email: EmailData
    is_selected: bool

class MatchResponse(BaseModel):
    jd_text: str
    candidates: List[CandidateResult]
    best_index: int

@router.post("/generate_jd")
async def api_generate_jd(payload: GenerateJDRequest):
    logger.info(f"Received JD generation request for {payload.job_title}")
    try:
        jd_text = await generate_jd(payload)
        logger.info(f"JD generated successfully")
        return {"jd_text": jd_text}
    except Exception as e:
        logger.error(f"Failed to generate JD: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate JD: {str(e)}")

@router.post("/match", response_model=MatchResponse)
async def api_match(
    jd_text: Optional[str] = Form(default=None),
    jd_file: Optional[UploadFile] = File(default=None),
    resumes: List[UploadFile] = File(default=[]),
):
    logger.info(f"Received match request with {len(resumes)} resumes")
    
    if not jd_text and not jd_file:
        raise HTTPException(status_code=400, detail="Provide jd_text or jd_file")
    if not resumes:
        raise HTTPException(status_code=400, detail="Provide at least one resume")
    
    try:
        if jd_file:
            logger.info(f"Extracting text from JD file: {jd_file.filename}")
            jd_text = await extract_text_from_upload(jd_file)
            logger.info(f"Extracted {len(jd_text)} characters from JD")
        
        texts = []
        filenames = []
        for f in resumes[:10]:
            logger.info(f"Extracting text from resume: {f.filename}")
            filenames.append(f.filename)
            resume_text = await extract_text_from_upload(f)
            texts.append(resume_text)
            logger.info(f"Extracted {len(resume_text)} characters from {f.filename}")
        
        logger.info("Starting AI matching process")
        ai_results = await ai_match_resumes(jd_text or "", texts, filenames)
        logger.info(f"AI matching completed with {len(ai_results)} results")
        
        best_index = max(range(len(ai_results)), key=lambda i: ai_results[i].score)
        logger.info(f"Best candidate index: {best_index} with score {ai_results[best_index].score}")
        
        candidates = []
        for i, r in enumerate(ai_results):
            is_selected = r.score >= 50
            logger.info(f"Generating email for candidate {i}: {filenames[i]} (score: {r.score}, selected: {is_selected})")
            
            if is_selected:
                email = await generate_interview_email(jd_text or "", texts[i], filenames[i])
            else:
                email = await generate_rejection_email(jd_text or "", texts[i], filenames[i])
            
            candidates.append(
                CandidateResult(
                    filename=r.filename or filenames[i],
                    score=r.score,
                    missing_skills=r.missing_skills,
                    remarks=r.remarks,
                    email=email,
                    is_selected=is_selected,
                )
            )
        
        logger.info("Match process completed successfully")
        return MatchResponse(jd_text=jd_text or "", candidates=candidates, best_index=best_index)
        
    except Exception as e:
        logger.error(f"Error in match endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process: {str(e)}")
