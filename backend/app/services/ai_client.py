import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import json
import logging
import re
from ..prompts.jd_generation import JD_GENERATION_SYSTEM, JD_GENERATION_USER_TEMPLATE
from ..prompts.resume_matching import RESUME_MATCHING_SYSTEM, RESUME_MATCHING_USER_TEMPLATE
from ..prompts.email_generation import (
    INTERVIEW_EMAIL_SYSTEM, INTERVIEW_EMAIL_USER_TEMPLATE,
    REJECTION_EMAIL_SYSTEM, REJECTION_EMAIL_USER_TEMPLATE
)

logger = logging.getLogger(__name__)

# AI Service Configuration
AI_MODEL_NAME = "gemini-2.5-flash"
AI_API_KEY_ENV = "GEMINI_API_KEY"

# Generation Configuration
DEFAULT_TEMPERATURE = 0.01
MATCHING_TEMPERATURE = 0.0  # Lower temperature for consistent JSON
MAX_TOKENS_JD = 1500
MAX_TOKENS_MATCHING = 3000  # Increased for better responses
MAX_TOKENS_EMAIL = 700
MAX_TOKENS_REJECTION = 500

# Initialize AI service
try:
    from google import genai
    AI_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import Google GenAI: {e}")
    genai = None
    AI_SERVICE_AVAILABLE = False

class GenerateJDInput(BaseModel):
    job_title: str
    years_experience: int
    must_have_skills: str
    company_name: str
    employment_type: str
    industry: str
    location: str

class MatchResult(BaseModel):
    filename: str
    score: int
    missing_skills: list[str]
    remarks: str

class EmailResult(BaseModel):
    subject: str
    body: str

def _get_ai_client() -> Optional[Any]:
    """
    Initialize and return AI client instance.
    Returns None if service is not available or API key is missing.
    """
    if not AI_SERVICE_AVAILABLE:
        logger.warning("AI service not available - SDK not installed")
        return None
    
    api_key = os.getenv(AI_API_KEY_ENV, "")
    if not api_key:
        logger.warning(f"{AI_API_KEY_ENV} not set in environment")
        return None
    
    try:
        # The client gets the API key from the environment variable automatically
        client = genai.Client()
        logger.info("AI client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize AI client: {e}")
        return None

async def generate_jd(payload: GenerateJDInput) -> str:
    logger.info(f"Generating JD for {payload.job_title} at {payload.company_name}")
    client = _get_ai_client()
    
    if client is None:
        logger.warning("No AI client available, using fallback JD generation")
        lines = []
        lines.append(f"# {payload.job_title}")
        lines.append(f"**{payload.company_name}**")
        lines.append("")
        lines.append(f"📍 {payload.location} | 💼 {payload.employment_type} | 🏢 {payload.industry}")
        lines.append("")
        lines.append("## Overview")
        lines.append(f"We are seeking a {payload.job_title} with {payload.years_experience}+ years of experience to join {payload.company_name}. The ideal candidate demonstrates strong ownership and collaboration across cross-functional teams.")
        lines.append("")
        lines.append("## Responsibilities")
        lines.append("- Deliver high-quality work aligned with product goals")
        lines.append("- Collaborate with stakeholders to refine requirements and scope")
        lines.append("- Write clean, reliable, and testable code")
        lines.append("- Participate in code reviews and continuous improvement")
        lines.append("")
        lines.append("## Requirements")
        lines.append(f"- {payload.years_experience}+ years relevant professional experience")
        lines.append("- Proven problem-solving and communication skills")
        for skill in [s.strip() for s in payload.must_have_skills.split(',') if s.strip()]:
            lines.append(f"- {skill}")
        lines.append("")
        lines.append("## Nice to Have")
        lines.append("- Exposure to adjacent tools and ecosystems")
        lines.append("- Experience in high-growth environments")
        lines.append("")
        lines.append("## Benefits")
        lines.append("- Competitive compensation and benefits")
        lines.append("- Flexible work environment")
        lines.append("- Learning stipend and growth opportunities")
        lines.append("")
        lines.append("## How to Apply")
        lines.append("Please submit your resume highlighting relevant experience.")
        return "\n".join(lines)
    
    system = JD_GENERATION_SYSTEM
    user = JD_GENERATION_USER_TEMPLATE.format(
        job_title=payload.job_title,
        company_name=payload.company_name,
        years_experience=payload.years_experience,
        must_have_skills=payload.must_have_skills,
        employment_type=payload.employment_type,
        industry=payload.industry,
        location=payload.location
    )
    
    try:
        logger.info(f"Calling AI API with model {AI_MODEL_NAME} for JD generation")
        prompt = f"{system}\n\n{user}"
        response = client.models.generate_content(
            model=AI_MODEL_NAME,
            contents=prompt
        )
        result = response.text.strip()
        logger.info(f"Successfully generated JD with {len(result)} characters")
        return result
    except Exception as e:
        logger.error(f"Error generating JD with AI: {e}")
        raise

class MatchAIItem(BaseModel):
    filename: str
    score: float
    missing_skills: List[str]
    remarks: str

def _extract_json_from_text(text: str) -> str:
    """
    Extract clean JSON from AI response text.
    Handles various formats and malformed responses.
    """
    text = text.strip()
    
    # Remove markdown code blocks
    if '```json' in text:
        match = re.search(r'```json\s*([\[\{].*?[\]\}])\s*```', text, re.DOTALL)
        if match:
            text = match.group(1)
    elif text.startswith('```'):
        text = re.sub(r'^```[a-z]*\n', '', text)
        text = re.sub(r'\n```$', '', text)
    
    # Find JSON array (preferred for matching results)
    # Look for complete JSON array with proper closing
    array_match = re.search(r'(\[.*?\])', text, re.DOTALL)
    if array_match:
        text = array_match.group(1)
    else:
        # Try to find incomplete array and complete it
        incomplete_match = re.search(r'(\[.*)', text, re.DOTALL)
        if incomplete_match:
            # Try to complete the array
            incomplete_text = incomplete_match.group(1)
            if not incomplete_text.endswith(']'):
                # Count open brackets and close them
                open_brackets = incomplete_text.count('[') - incomplete_text.count(']')
                if open_brackets > 0:
                    incomplete_text += ']' * open_brackets
                text = incomplete_text
        else:
            # Fallback to object
            object_match = re.search(r'(\{.*?\})', text, re.DOTALL)
            if object_match:
                text = object_match.group(1)
    
    # Clean up common JSON issues
    text = re.sub(r'"([^"]+)"\s+is\s+(?:not\s+)?(?:missing|present)[^,\n\]]*,?', r'"\1",', text)
    text = re.sub(r'"\s*,\s*\n\s*"', '",\n"', text)
    text = re.sub(r'"\s*\n\s*"', '",\n"', text)
    text = re.sub(r',\s*([}\]])', r'\1', text)
    
    # Fix unquoted values
    text = re.sub(r':\s*([^",\{\[\s][^,\}\]]*?)(?=\s*[,\}])', r': "\1"', text)
    
    # Remove any trailing content after the JSON
    # Find the end of the JSON structure
    if text.startswith('['):
        bracket_count = 0
        for i, char in enumerate(text):
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    text = text[:i+1]
                    break
    elif text.startswith('{'):
        brace_count = 0
        for i, char in enumerate(text):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    text = text[:i+1]
                    break
    
    return text.strip()

def _tokenize(text: str) -> List[str]:
    return [t for t in re.split(r"[^a-zA-Z0-9+#\.]+", text.lower()) if t]

def _canonical_skills(text: str) -> List[str]:
    keywords = [
        "python","java","javascript","typescript","react","node","fastapi","django","flask",
        "aws","gcp","azure","docker","kubernetes","sql","nosql","postgres","mysql","mongodb",
        "nlp","ml","ai","pytorch","tensorflow","sklearn","spacy","transformers","langchain",
        "llm","genai","huggingface","openai","groq","llama","whisper","opencv","computer","vision",
        "data","engineering","mle","mlops","airflow","kubeflow","ray","pandas","numpy","scipy",
        "c++","c#","go","rust","php","html","css","tailwind","next.js","nextjs","redux","jest"
    ]
    set_kw = set(keywords)
    seen = set()
    out: List[str] = []
    for tok in _tokenize(text):
        if tok in set_kw and tok not in seen:
            seen.add(tok)
            out.append(tok)
    return out

def _extract_jd_metadata(jd_text: str) -> dict:
    lines = jd_text.split('\n')
    job_title = "Position"
    company_name = "Our Company"
    
    for i, line in enumerate(lines[:15]):
        line_clean = line.strip().replace('#', '').strip()
        
        if i == 0 and line_clean and len(line_clean) < 100:
            job_title = line_clean
        
        if any(keyword in line_clean.lower() for keyword in ['company:', 'at ', 'join ']):
            words = line_clean.split()
            for j, word in enumerate(words):
                if word.lower() in ['at', 'join', 'company:'] and j + 1 < len(words):
                    company_name = ' '.join(words[j+1:j+4]).strip('.,')
                    break
        
        if '**' in line and i < 5:
            match = re.search(r'\*\*([^*]+)\*\*', line)
            if match:
                potential_company = match.group(1).strip()
                if len(potential_company) < 50 and not any(x in potential_company.lower() for x in ['overview', 'description', 'responsibilities']):
                    company_name = potential_company
    
    return {"job_title": job_title, "company_name": company_name}

async def ai_match_resumes(jd_text: str, resumes_text: List[str], filenames: List[str]) -> List[MatchAIItem]:
    logger.info(f"AI matching {len(resumes_text)} resumes against JD")
    client = _get_ai_client()
    
    if client is None:
        logger.error("No AI client available for matching")
        raise Exception(f"AI service not available - {AI_API_KEY_ENV} not configured")
    
    jd_skills = _canonical_skills(jd_text)
    system = RESUME_MATCHING_SYSTEM
    
    candidates_data = []
    for i, txt in enumerate(resumes_text):
        candidates_data.append({
            "filename": filenames[i],
            "resume_text": txt[:6000]
        })
    
    rubric = {
        "instructions": "Analyze resume against FULL job description context. Consider role level, experience requirements, and all job responsibilities. Match skills from jd_skills list if clearly present in resume_text (exact or close variant).",
        "scoring": "score = round(100 * matched_count / max(1, len(jd_skills))). Consider role seniority and experience level from full JD context.",
        "output_format": {
            "filename": "string",
            "score": "0-100 integer",
            "missing_skills": "array of strings; subset of jd_skills not matched",
            "remarks": "one concise sentence highlighting 1-2 strengths and gaps, considering role level and experience requirements"
        }
    }
    # Format candidates data for the template
    candidates_text = ""
    for candidate in candidates_data:
        candidates_text += f"Filename: {candidate['filename']}\n"
        candidates_text += f"Resume: {candidate['resume_text']}\n\n"
    
    user = RESUME_MATCHING_USER_TEMPLATE.format(
        jd_full_content=jd_text,
        jd_skills=jd_skills,
        candidates=candidates_text
    )
    
    try:
        logger.info(f"Calling AI API for resume matching with structured output")
        prompt = f"{system}\n\n{user}"
        response = client.models.generate_content(
            model=AI_MODEL_NAME,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[MatchResult],
            }
        )
        
        # Use the structured response
        results: list[MatchResult] = response.parsed
        logger.info(f"Successfully parsed {len(results)} results")
        
        out: List[MatchAIItem] = []
        for result in results:
            out.append(
                MatchAIItem(
                    filename=result.filename,
                    score=float(result.score),
                    missing_skills=result.missing_skills,
                    remarks=result.remarks,
                )
            )
        return out
        
    except Exception as e:
        logger.error(f"AI matching failed: {e}")
        # Create fallback results when API call fails
        logger.warning("Creating fallback results due to API error")
        fallback_results = []
        for i, filename in enumerate(filenames):
            fallback_results.append(
                MatchAIItem(
                    filename=filename,
                    score=0.0,
                    missing_skills=jd_skills,
                    remarks="Unable to analyze - API error"
                )
            )
        return fallback_results

async def generate_interview_email(jd_text: str, resume_text: str, filename: str) -> dict:
    logger.info(f"Generating interview email for {filename}")
    client = _get_ai_client()
    name = os.path.splitext(os.path.basename(filename))[0].replace("_", " ").title()
    
    metadata = _extract_jd_metadata(jd_text)
    job_title = metadata["job_title"].replace("*", "").strip()
    company_name = metadata["company_name"].replace("*", "").strip()
    
    if client is None:
        logger.warning("No AI client, using fallback interview email")
        return {
            "subject": f"Interview Invitation - {job_title}",
            "body": f"Dear {name},\n\nWe are impressed with your qualifications for the {job_title} position. We would like to invite you for an interview.\n\nPlease share your availability for next week.\n\nBest regards,\nHiring Team"
        }
    
    clean_jd = jd_text.replace("*", "").replace("#", "")[:4000]  # Increased for better context
    clean_resume = resume_text[:2000]
    
    system = INTERVIEW_EMAIL_SYSTEM
    user = INTERVIEW_EMAIL_USER_TEMPLATE.format(
        job_title=job_title,
        company_name=company_name,
        candidate_name=name,
        jd_summary=clean_jd,
        resume_summary=clean_resume
    )
    
    try:
        prompt = f"{system}\n\n{user}"
        response = client.models.generate_content(
            model=AI_MODEL_NAME,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": EmailResult,
            }
        )
        
        # Use the structured response
        email_result: EmailResult = response.parsed
        logger.info("Interview email generated successfully")
        return {"subject": email_result.subject, "body": email_result.body}
    except Exception as e:
        logger.warning(f"Email generation failed: {e}")
        return {
            "subject": f"Interview Invitation - {job_title} at {company_name}",
            "body": f"Dear {name},\n\nWe are impressed with your qualifications for the {job_title} position at {company_name}. We would like to invite you for an interview.\n\nPlease share your availability for next week.\n\nBest regards,\nHiring Team"
        }

async def generate_rejection_email(jd_text: str, resume_text: str, filename: str) -> dict:
    logger.info(f"Generating rejection email for {filename}")
    client = _get_ai_client()
    name = os.path.splitext(os.path.basename(filename))[0].replace("_", " ").title()
    
    metadata = _extract_jd_metadata(jd_text)
    job_title = metadata["job_title"].replace("*", "").strip()
    company_name = metadata["company_name"].replace("*", "").strip()
    
    if client is None:
        logger.warning("No AI client, using fallback rejection email")
        return {
            "subject": f"Application Status - {job_title}",
            "body": f"Dear {name},\n\nThank you for your interest in the {job_title} position. We have decided to move forward with other candidates.\n\nWe wish you success in your job search.\n\nBest regards,\nHiring Team"
        }
    
    clean_jd = jd_text.replace("*", "").replace("#", "")[:4000]  # Match interview email
    
    system = REJECTION_EMAIL_SYSTEM
    user = REJECTION_EMAIL_USER_TEMPLATE.format(
        job_title=job_title,
        company_name=company_name,
        candidate_name=name,
        jd_summary=clean_jd,
        resume_summary=resume_text[:500] + "..." if len(resume_text) > 500 else resume_text
    )
    
    try:
        prompt = f"{system}\n\n{user}"
        response = client.models.generate_content(
            model=AI_MODEL_NAME,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": EmailResult,
            }
        )
        
        # Use the structured response
        email_result: EmailResult = response.parsed
        logger.info("Rejection email generated successfully")
        return {"subject": email_result.subject, "body": email_result.body}
    except Exception as e:
        logger.warning(f"Rejection email generation failed: {e}")
        return {
            "subject": f"Application Status - {job_title} at {company_name}",
            "body": f"Dear {name},\n\nThank you for your interest in the {job_title} position at {company_name}. After careful review, we have decided to move forward with other candidates.\n\nWe wish you the best in your job search.\n\nBest regards,\nHiring Team"
        }
