import { useState, type FormEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'

const outputOptions = [
  { id: 'suggestions', label: 'Suggestions' },
  { id: 'resume', label: 'Tailored resume' },
  { id: 'cover_letter', label: 'Cover letter' },
] as const

const outputFiles = {
  suggestions: 'job_analysis.md',
  resume: 'tailored_resume.md',
  cover_letter: 'cover_letter.md',
} as const

type OutputId = (typeof outputOptions)[number]['id']
type Results = Partial<Record<OutputId, string>>

const maxResumeSize = 10 * 1024 * 1024
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, '') ?? ''

function App() {
  const [resume, setResume] = useState<File | null>(null)
  const [jobDescription, setJobDescription] = useState('')
  const [selectedOutputs, setSelectedOutputs] = useState<OutputId[]>([
    'suggestions',
  ])
  const [results, setResults] = useState<Results>({})
  const [activeResult, setActiveResult] = useState<OutputId | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const resumeNeeded = selectedOutputs.some(
    (output) => output === 'resume' || output === 'cover_letter',
  )
  const resumeTooLarge = resume !== null && resume.size > maxResumeSize
  const resultOptions = outputOptions.filter((option) => results[option.id])
  const currentResult = activeResult ? results[activeResult] : undefined
  const canSubmit =
    jobDescription.trim().length > 0 &&
    selectedOutputs.length > 0 &&
    (!resumeNeeded || resume !== null) &&
    !resumeTooLarge &&
    !busy

  function toggleOutput(output: OutputId) {
    setSelectedOutputs((current) =>
      current.includes(output)
        ? current.filter((item) => item !== output)
        : [...current, output],
    )
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!canSubmit) return

    setBusy(true)
    setError('')
    setResults({})
    setActiveResult(null)

    const formData = new FormData()
    formData.set('job_description', jobDescription.trim())
    selectedOutputs.forEach((output) => formData.append('deliverables', output))
    if (resume) formData.set('resume_file', resume)

    try {
      const response = await fetch(`${apiBaseUrl}/api/generate`, {
        method: 'POST',
        body: formData,
      })
      const payload = (await response.json().catch(() => null)) as
        | { detail?: string; results?: Results }
        | null

      if (!response.ok) {
        throw new Error(payload?.detail ?? 'Could not generate your documents.')
      }
      if (!payload?.results || Object.keys(payload.results).length === 0) {
        throw new Error('The run finished without returning any documents.')
      }

      setResults(payload.results)
      setActiveResult(
        outputOptions.find((option) => payload.results?.[option.id])?.id ?? null,
      )
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Something went wrong. Please try again.',
      )
    } finally {
      setBusy(false)
    }
  }

  function downloadResult() {
    if (!activeResult || !currentResult) return

    const blob = new Blob([currentResult], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = outputFiles[activeResult]
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <main className="page">
      <header className="page-header">
        <h1>Resume Tailor</h1>
      </header>

      <div className="workspace">
        <form className="panel inputs" onSubmit={handleSubmit}>
          <h2>Job details</h2>

          <div className="field">
            <label htmlFor="resume-file">
              Resume <span>{resumeNeeded ? 'Required' : 'Optional'}</span>
            </label>
            <input
              id="resume-file"
              type="file"
              accept=".pdf,.txt,.md"
              onChange={(event) => setResume(event.target.files?.[0] ?? null)}
            />
            <small>PDF, TXT, or Markdown. Maximum 10 MB.</small>
            {resumeTooLarge && (
              <p className="field-error" role="alert">
                Choose a file smaller than 10 MB.
              </p>
            )}
          </div>

          {resume && (
            <button
              className="text-button remove-resume"
              type="button"
              onClick={() => setResume(null)}
            >
              Remove {resume.name}
            </button>
          )}

          <div className="field job-field">
            <label htmlFor="job-description">Job description</label>
            <textarea
              id="job-description"
              value={jobDescription}
              onChange={(event) => setJobDescription(event.target.value)}
              placeholder="Paste the job description"
              rows={12}
              required
            />
          </div>

          <fieldset className="field output-field">
            <legend>Create</legend>
            <div className="output-options">
              {outputOptions.map((option) => (
                <label key={option.id}>
                  <input
                    type="checkbox"
                    checked={selectedOutputs.includes(option.id)}
                    onChange={() => toggleOutput(option.id)}
                  />
                  {option.label}
                </label>
              ))}
            </div>
          </fieldset>

          {resumeNeeded && !resume && (
            <p className="field-error">
              Upload a resume to create a tailored resume or cover letter.
            </p>
          )}
          {error && <p className="error-message" role="alert">{error}</p>}

          <button className="submit-button" type="submit" disabled={!canSubmit}>
            {busy ? 'Generating…' : 'Generate'}
          </button>
          <p className="privacy-note">
            Your files are sent to the configured model provider. Results are
            saved locally.
          </p>
        </form>

        <section className="panel results" aria-label="Generated results">
          <div className="results-heading">
            <h2>Results</h2>
            {currentResult && (
              <button
                className="text-button"
                type="button"
                onClick={downloadResult}
              >
                Download
              </button>
            )}
          </div>

          {busy ? (
            <p className="empty-state" aria-live="polite">
              Generating your materials…
            </p>
          ) : resultOptions.length > 0 && currentResult ? (
            <>
              <div className="result-tabs" role="tablist" aria-label="Results">
                {resultOptions.map((option) => (
                  <button
                    className={activeResult === option.id ? 'active' : ''}
                    key={option.id}
                    type="button"
                    role="tab"
                    aria-selected={activeResult === option.id}
                    onClick={() => setActiveResult(option.id)}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
              <article className="markdown-output">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {currentResult}
                </ReactMarkdown>
              </article>
            </>
          ) : (
            <p className="empty-state">Generated materials will appear here.</p>
          )}
        </section>
      </div>
    </main>
  )
}

export default App
