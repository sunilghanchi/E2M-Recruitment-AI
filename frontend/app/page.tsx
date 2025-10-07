"use client"
import { useMemo, useState } from 'react'
import ReactMarkdown from 'react-markdown'

type EmailData = {
  subject: string
  body: string
}

type Candidate = {
  filename: string
  score: number
  missing_skills: string[]
  remarks: string
  email: EmailData
  is_selected: boolean
}

type MatchResponse = {
  jd_text: string
  candidates: Candidate[]
  best_index: number
}

type ToastType = 'error' | 'success' | 'info'

export default function Page() {
  const [jdText, setJdText] = useState('')
  const [jdFile, setJdFile] = useState<File | null>(null)
  const [resumes, setResumes] = useState<File[]>([])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<MatchResponse | null>(null)
  const [activeTab, setActiveTab] = useState<'manual' | 'upload' | 'generate'>('manual')
  const [toast, setToast] = useState<{ text: string; type: ToastType } | null>(null)
  const [selectedCandidate, setSelectedCandidate] = useState<number | null>(null)
  const [editedEmails, setEditedEmails] = useState<Record<number, EmailData>>({})

  const [genFields, setGenFields] = useState({
    job_title: '',
    years_experience: 3,
    must_have_skills: '',
    company_name: '',
    employment_type: 'Full-time',
    industry: '',
    location: ''
  })

  const notify = (text: string, type: ToastType = 'info') => {
    setToast({ text, type })
    const timer = setTimeout(() => setToast(null), 3500)
    return () => clearTimeout(timer)
  }

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text).then(() => {
      notify(`${label} copied`, 'success')
    }).catch(() => {
      notify('Failed to copy', 'error')
    })
  }

  const bestCandidate = useMemo(() => {
    if (!result) return null
    return result.candidates[result.best_index]
  }, [result])

  const getCurrentEmail = (index: number): EmailData => {
    if (editedEmails[index]) return editedEmails[index]
    if (result?.candidates[index]) return result.candidates[index].email
    return { subject: '', body: '' }
  }

  const updateEmail = (index: number, field: 'subject' | 'body', value: string) => {
    const current = getCurrentEmail(index)
    setEditedEmails(prev => ({
      ...prev,
      [index]: { ...current, [field]: value }
    }))
  }

  const onSelectJDFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null
    setJdFile(file)
    if (file) {
      setActiveTab('upload')
      notify(`Selected: ${file.name}`, 'info')
    }
  }

  const onSelectResumes = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    const selected = files.slice(0, 10)
    setResumes(selected)
    notify(`${selected.length} resume(s) selected`, 'info')
  }

  const submit = async () => {
    if ((!jdText && !jdFile) || resumes.length === 0) {
      notify('Provide a job description and at least one resume', 'error')
      return
    }

    setLoading(true)
    setResult(null)
    setSelectedCandidate(null)
    setEditedEmails({})

    try {
      const form = new FormData()
      if (jdFile) form.append('jd_file', jdFile)
      if (jdText && !jdFile) form.append('jd_text', jdText)
      resumes.forEach(f => form.append('resumes', f))
      
      const base = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'
      const resp = await fetch(`${base}/api/match`, { 
        method: 'POST', 
        body: form 
      })
      
      if (!resp.ok) {
        const error = await resp.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(error.detail || 'Failed to process')
      }
      
      const data: MatchResponse = await resp.json()
      setResult(data)
      setSelectedCandidate(data.best_index)
      notify('AI matching completed successfully', 'success')
    } catch (err: any) {
      notify(err.message || 'Error processing. Check backend logs.', 'error')
    } finally {
      setLoading(false)
    }
  }

  const generateJD = async () => {
    if (!genFields.job_title || !genFields.company_name) {
      notify('Fill job title and company name', 'error')
      return
    }

    setLoading(true)
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'
      const resp = await fetch(`${base}/api/generate_jd`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(genFields)
      })
      
      if (!resp.ok) {
        const error = await resp.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(error.detail || 'Failed to generate')
      }
      
      const data = await resp.json()
      setJdText(data.jd_text)
      setActiveTab('manual')
      notify('AI generated JD successfully', 'success')
    } catch (err: any) {
      notify(err.message || 'Error generating JD. Check backend logs.', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark via-dark-secondary to-dark overflow-x-hidden">
      <div className="container mx-auto px-4 py-6 md:py-8 max-w-7xl">
        <header className="text-center mb-8 md:mb-12">
          <h1 className="text-3xl md:text-5xl font-bold mb-3 md:mb-4">
            <span className="gradient-text">Recruitment AI Agent</span>
          </h1>
          <p className="text-gray-400 text-sm md:text-lg">AI-powered candidate matching and email generation</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8">
          <section className="space-y-4 md:space-y-6">
            <div className="card">
              <h2 className="text-xl md:text-2xl font-semibold mb-4 flex items-center gap-2">
                <span className="w-2 h-2 bg-primary rounded-full"></span>
                Job Description
              </h2>

              <div className="flex gap-2 mb-4 flex-wrap">
                {(['manual', 'upload', 'generate'] as const).map(tab => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-3 md:px-4 py-2 rounded-lg transition-all text-sm md:text-base ${
                      activeTab === tab ? 'bg-primary text-white' : 'bg-dark-tertiary text-gray-400'
                    }`}
                  >
                    {tab.charAt(0).toUpperCase() + tab.slice(1)}
                  </button>
                ))}
              </div>

              {activeTab === 'manual' && (
                <>
                  <textarea
                    value={jdText}
                    onChange={e => setJdText(e.target.value)}
                    placeholder="Paste or type job description here..."
                    className="w-full h-40 md:h-48 resize-none text-sm md:text-base"
                  />
                  {jdText && (
                    <div className="mt-3 p-3 md:p-4 bg-dark border border-gray-800 rounded-lg max-h-64 overflow-y-auto">
                      <div className="text-xs text-gray-500 mb-2">Preview:</div>
                      <ReactMarkdown className="prose prose-invert prose-sm max-w-none prose-headings:text-primary prose-headings:font-semibold prose-p:text-gray-300 prose-li:text-gray-300 prose-strong:text-gray-100">
                        {jdText}
                      </ReactMarkdown>
                    </div>
                  )}
                </>
              )}

              {activeTab === 'upload' && (
                <div className="border-2 border-dashed border-gray-700 rounded-lg p-6 md:p-8 text-center hover:border-primary transition-all">
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={onSelectJDFile}
                    className="hidden"
                    id="jd-file"
                  />
                  <label htmlFor="jd-file" className="cursor-pointer block">
                    <div className="text-3xl md:text-4xl mb-2">📄</div>
                    <p className="text-gray-400 text-sm md:text-base">
                      {jdFile ? jdFile.name : 'Click to upload PDF or DOCX'}
                    </p>
                  </label>
                </div>
              )}

              {activeTab === 'generate' && (
                <div className="space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <input
                      placeholder="Job Title"
                      value={genFields.job_title}
                      onChange={e => setGenFields(s => ({ ...s, job_title: e.target.value }))}
                      className="text-sm md:text-base"
                    />
                    <input
                      placeholder="Years of Experience"
                      type="number"
                      value={genFields.years_experience}
                      onChange={e => setGenFields(s => ({ ...s, years_experience: Number(e.target.value) }))}
                      className="text-sm md:text-base"
                    />
                  </div>
                  <input
                    placeholder="Must-have Skills (comma-separated)"
                    value={genFields.must_have_skills}
                    onChange={e => setGenFields(s => ({ ...s, must_have_skills: e.target.value }))}
                    className="text-sm md:text-base"
                  />
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <input
                      placeholder="Company Name"
                      value={genFields.company_name}
                      onChange={e => setGenFields(s => ({ ...s, company_name: e.target.value }))}
                      className="text-sm md:text-base"
                    />
                    <select
                      value={genFields.employment_type}
                      onChange={e => setGenFields(s => ({ ...s, employment_type: e.target.value }))}
                      className="text-sm md:text-base"
                    >
                      <option>Full-time</option>
                      <option>Part-time</option>
                      <option>Contract</option>
                    </select>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <input
                      placeholder="Industry"
                      value={genFields.industry}
                      onChange={e => setGenFields(s => ({ ...s, industry: e.target.value }))}
                      className="text-sm md:text-base"
                    />
                    <input
                      placeholder="Location"
                      value={genFields.location}
                      onChange={e => setGenFields(s => ({ ...s, location: e.target.value }))}
                      className="text-sm md:text-base"
                    />
                  </div>
                  <button 
                    onClick={generateJD} 
                    disabled={loading}
                    className="btn-primary w-full text-sm md:text-base"
                  >
                    {loading ? '⚙️ Generating...' : '🤖 Generate JD with AI'}
                  </button>
                </div>
              )}
            </div>

            <div className="card">
              <h2 className="text-xl md:text-2xl font-semibold mb-4 flex items-center gap-2">
                <span className="w-2 h-2 bg-primary rounded-full"></span>
                Resumes (up to 10)
              </h2>
              <div className="border-2 border-dashed border-gray-700 rounded-lg p-6 md:p-8 text-center hover:border-primary transition-all">
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  multiple
                  onChange={onSelectResumes}
                  className="hidden"
                  id="resume-files"
                />
                <label htmlFor="resume-files" className="cursor-pointer block">
                  <div className="text-3xl md:text-4xl mb-2">📋</div>
                  <p className="text-gray-400 text-sm md:text-base">
                    {resumes.length > 0 ? `${resumes.length} file(s) selected` : 'Click to upload resumes'}
                  </p>
                  {resumes.length > 0 && (
                    <div className="mt-3 text-xs md:text-sm text-gray-500 break-words">
                      {resumes.map(f => f.name).join(', ')}
                    </div>
                  )}
                </label>
              </div>

              <button
                onClick={submit}
                disabled={loading}
                className="btn-primary w-full mt-4 text-sm md:text-base"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin">⚙️</span> AI Processing...
                  </span>
                ) : (
                  '🚀 Match with AI'
                )}
              </button>
            </div>
          </section>

          <section className="space-y-4 md:space-y-6">
            {result && (
              <>
                <div className="card">
                  <h2 className="text-xl md:text-2xl font-semibold mb-4 flex items-center gap-2">
                    <span className="w-2 h-2 bg-primary rounded-full"></span>
                    AI Results
                  </h2>
                  <div className="space-y-3">
                    {result.candidates.map((c, i) => (
                      <div
                        key={i}
                        onClick={() => setSelectedCandidate(i)}
                        className={`p-3 md:p-4 rounded-lg border-2 transition-all cursor-pointer ${
                          selectedCandidate === i
                            ? 'border-primary bg-primary/10'
                            : c.score < 50
                            ? 'border-red-900/50 bg-red-950/20 hover:border-red-800'
                            : 'border-gray-800 bg-dark-tertiary hover:border-gray-700'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2 flex-1 min-w-0">
                            {c.is_selected ? (
                              <span className="text-lg md:text-xl flex-shrink-0">✅</span>
                            ) : (
                              <span className="text-lg md:text-xl flex-shrink-0">❌</span>
                            )}
                            {i === result.best_index && <span className="text-lg md:text-xl flex-shrink-0">⭐</span>}
                            <div className="font-semibold truncate text-sm md:text-base">{c.filename}</div>
                          </div>
                          <div className="flex items-center gap-1 md:gap-2 flex-shrink-0">
                            <span className={`text-xl md:text-2xl font-bold ${
                              c.score >= 50 ? 'text-green-400' : 'text-red-400'
                            }`}>
                              {c.score}
                            </span>
                            <span className="text-gray-500 text-xs md:text-sm">/100</span>
                          </div>
                        </div>
                        <div className="text-xs md:text-sm text-gray-400 mb-1">
                          <span className="text-gray-500">AI Remarks:</span> {c.remarks}
                        </div>
                        {c.missing_skills.length > 0 && (
                          <div className="text-xs md:text-sm text-orange-400">
                            <span className="text-gray-500">Missing:</span> {c.missing_skills.join(', ')}
                          </div>
                        )}
                        <div className="mt-2">
                          <span className={`text-xs px-2 py-1 rounded ${
                            c.is_selected 
                              ? 'bg-green-900/30 text-green-400 border border-green-800' 
                              : 'bg-red-900/30 text-red-400 border border-red-800'
                          }`}>
                            {c.is_selected ? 'Selected for Interview' : 'Not Selected'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {selectedCandidate !== null && result.candidates[selectedCandidate] && (
                  <div className="card">
                    <h2 className="text-xl md:text-2xl font-semibold mb-4 flex items-center gap-2">
                      <span className="w-2 h-2 bg-primary rounded-full"></span>
                      AI Generated Email
                    </h2>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {result.candidates[selectedCandidate].is_selected ? (
                            <span className="text-green-400 text-sm md:text-base font-semibold">✉️ Interview Invitation</span>
                          ) : (
                            <span className="text-red-400 text-sm md:text-base font-semibold">📧 Rejection Email</span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500">
                          Score: {result.candidates[selectedCandidate].score < 50 ? 'Below 50 - Auto Rejected' : '50+ - Selected'}
                        </div>
                      </div>

                      <div className="space-y-3">
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <label className="text-xs md:text-sm font-semibold text-gray-400">Subject Line</label>
                            <button
                              onClick={() => copyToClipboard(getCurrentEmail(selectedCandidate).subject, 'Subject')}
                              className="text-xs px-2 py-1 bg-dark-tertiary hover:bg-gray-700 rounded transition-all"
                            >
                              📋 Copy
                            </button>
                          </div>
                          <input
                            type="text"
                            value={getCurrentEmail(selectedCandidate).subject}
                            onChange={e => updateEmail(selectedCandidate, 'subject', e.target.value)}
                            className="w-full bg-dark border border-gray-700 rounded-lg px-3 py-2 text-sm md:text-base focus:border-primary"
                          />
                        </div>

                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <label className="text-xs md:text-sm font-semibold text-gray-400">Email Body</label>
                            <button
                              onClick={() => copyToClipboard(getCurrentEmail(selectedCandidate).body, 'Email body')}
                              className="text-xs px-2 py-1 bg-dark-tertiary hover:bg-gray-700 rounded transition-all"
                            >
                              📋 Copy
                            </button>
                          </div>
                          <textarea
                            value={getCurrentEmail(selectedCandidate).body}
                            onChange={e => updateEmail(selectedCandidate, 'body', e.target.value)}
                            className="w-full bg-dark border border-gray-700 rounded-lg px-3 py-2 text-sm md:text-base h-48 resize-none focus:border-primary"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}

            {!result && (
              <div className="card text-center py-12 md:py-16">
                <div className="text-5xl md:text-6xl mb-4">🎯</div>
                <p className="text-gray-400 text-sm md:text-base px-4">
                  Upload resumes and JD to see AI-powered matching results
                </p>
              </div>
            )}
          </section>
        </div>
      </div>

      {toast && (
        <div className="fixed bottom-4 right-4 left-4 md:left-auto md:bottom-6 md:right-6 z-50">
          <div
            className={`px-4 md:px-5 py-2.5 md:py-3 rounded-lg shadow-lg border text-sm md:text-base ${
              toast.type === 'success'
                ? 'bg-green-600/90 border-green-500 text-white'
                : toast.type === 'error'
                ? 'bg-red-600/90 border-red-500 text-white'
                : 'bg-gray-800/90 border-gray-700 text-gray-100'
            }`}
          >
            {toast.text}
          </div>
        </div>
      )}
    </div>
  )
}
