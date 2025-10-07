# Recruitment AI Agent

FastAPI backend with Next.js frontend for job description intake, resume uploads, candidate scoring, and AI-powered email generation.

## Setup Instructions

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variable for Google Gemini API:
```bash
set GEMINI_API_KEY=your_gemini_api_key_here
```

**Get your Gemini API key:**
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API Key" 
4. Create a new API key
5. Copy the key and set it as the environment variable above

5. Run the FastAPI server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will run on `http://localhost:8000`
API documentation available at `http://localhost:8000/docs`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

Frontend will run on `http://localhost:3000`

## AI Model Choice

### Google Gemini with `gemini-2.5-flash`

**Why this model:**
- Advanced multimodal AI capabilities from Google
- Excellent language understanding and generation
- Strong reasoning capabilities for complex tasks
- Cost-effective with excellent quality
- Fast inference speeds enable real-time user experience
- Superior JSON output formatting for structured data
- Free tier available with generous limits

**Complete AI Integration - Everything Powered by AI:**

1. **JD Generation (AI-Powered)** 
   - Creates professional, structured job descriptions
   - Generates Overview, Responsibilities, Requirements, Benefits sections
   - Personalized to company, role, and industry

2. **Resume Matching (AI-Powered)**
   - Intelligent candidate scoring (0-100)
   - Contextual skill gap analysis
   - AI-generated remarks explaining each score
   - Deep understanding of role requirements vs candidate experience

3. **Email Generation (AI-Powered)**
   - Separate subject line and email body generation
   - **Smart Selection Logic**: Score >= 50 → Interview invitation, Score < 50 → Rejection email
   - Personalized interview invitations for qualified candidates
   - Professional rejection emails for candidates below threshold
   - Context-aware based on JD and resume content
   - Warm, human-like HR department communication
   - Editable subject and body fields
   - One-click copy functionality for both subject and body

### Debugging & Monitoring

Backend includes comprehensive logging:
- API call tracking
- Success/failure reporting
- Performance metrics
- Error details for troubleshooting

Check terminal output for real-time AI operation logs.

## How It Works

### Job Description Input
Three ways to provide JD:
1. **Manual Input** - Paste text directly
2. **File Upload** - Upload PDF or DOCX files
3. **AI Generation** - Provide job details and generate JD using AI

### Resume Processing
- Upload up to 10 resumes (PDF or DOCX)
- Text extraction using pypdf and python-docx
- Automatic scoring against JD requirements
- Missing skills identification
- Best candidate highlighting

### Results Display
- Candidate list with scores and remarks
- Best match highlighted with green border
- AI-generated interview invitation for top candidate
- Rejection email templates for other candidates

## Example Test Case

**Sample JD Requirements:**
- Job Title: Frontend Developer
- Skills: React, Next.js, TypeScript, Tailwind CSS
- Experience: 3+ years

Upload resumes with varying skill sets to see matching scores and AI-generated emails.

## Technical Stack

**Backend:**
- FastAPI for REST API
- Google GenAI SDK with `gemini-2.5-flash` model
- pypdf for PDF extraction
- python-docx for DOCX parsing
- CORS enabled for frontend integration
- **Structured Prompts Module** - Centralized AI prompt management

**Frontend:**
- Next.js 14 with App Router
- Tailwind CSS with custom black/orange gradient theme
- TypeScript for type safety
- Real-time API integration
- Responsive design with modern UI/UX

## Prompt Engineering Architecture

All AI prompts are managed in dedicated modules for maintainability:

```
backend/app/prompts/
├── jd_generation.py       # Job description generation prompts
├── resume_matching.py     # Resume analysis and scoring prompts
└── email_generation.py    # Interview and rejection email prompts
```

**Benefits:**
- Easy to update and version control prompts
- Clear separation of concerns
- Consistent prompt quality across the application
- Better collaboration on prompt engineering
- Detailed, structured instructions for AI models

## Features Implemented

✅ **Job Description Input (3 ways)**
- Manual text input
- File upload (PDF/DOCX)
- AI generation from structured fields

✅ **Resume Processing**
- Upload up to 10 resumes
- PDF and DOCX support
- Text extraction and parsing

✅ **Candidate Matching**
- Skill-based scoring (0-100)
- Missing skills identification
- Detailed remarks for each candidate
- Best match highlighting

✅ **AI Email Generation**
- Personalized interview invitations
- Professional rejection emails
- Uses Google GenAI for natural language

✅ **Modern UI/UX**
- Black and orange gradient theme
- Interactive tabs and forms
- Real-time feedback
- Error handling

## Quick Start (Windows)

1. Backend: Double-click `start-backend.bat` (edit to add your GEMINI_API_KEY)
2. Frontend: Double-click `start-frontend.bat`
3. Open: `http://localhost:3000`

## API Endpoints

- `GET /health` - Health check
- `POST /api/generate_jd` - Generate job description
- `POST /api/match` - Match resumes to JD

Full API docs: `http://localhost:8000/docs`

## Notes

- Graceful fallback if `GEMINI_API_KEY` not set
- Support for PDF and DOCX formats
- Responsive design works on all screen sizes
- Real-time processing with loading states

