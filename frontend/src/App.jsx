import { useRef, useState } from 'react'
import {
  AlertTriangle,
  ArrowDownToLine,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronDown,
  Clipboard,
  FileCheck2,
  FileText,
  FileUp,
  Info,
  LoaderCircle,
  LockKeyhole,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  X,
} from 'lucide-react'
import { simplifyPdf, simplifyText } from './services/api.js'

const MAX_FILE_BYTES = 15 * 1024 * 1024
const MAX_TEXT_CHARS = 100_000

const resultSections = [
  { key: 'required_documents', title: 'Required documents', marker: '01' },
  { key: 'eligibility_conditions', title: 'Eligibility conditions', marker: '02' },
  { key: 'step_by_step_instructions', title: 'Steps to take', marker: '03' },
  { key: 'important_warnings', title: 'Important warnings', marker: '04' },
  { key: 'deadlines_and_fees', title: 'Deadlines & fees', marker: '05' },
  { key: 'unclear_information', title: 'Needs a closer look', marker: '06' },
]

function formatBytes(bytes) {
  return bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(0)} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

async function makeReport(result) {
  const { jsPDF } = await import('jspdf')
  const pdf = new jsPDF()
  const margin = 17
  const width = pdf.internal.pageSize.getWidth() - margin * 2
  let y = 20
  const writeBlock = (heading, text) => {
    const lines = pdf.splitTextToSize(text || 'No information listed.', width)
    const requiredHeight = 8 + lines.length * 5
    if (y + requiredHeight > 278) {
      pdf.addPage()
      y = 20
    }
    pdf.setFont('helvetica', 'bold')
    pdf.setFontSize(12)
    pdf.text(heading, margin, y)
    y += 7
    pdf.setFont('helvetica', 'normal')
    pdf.setFontSize(10)
    pdf.text(lines, margin, y)
    y += lines.length * 5 + 7
  }

  pdf.setFont('helvetica', 'bold')
  pdf.setFontSize(19)
  pdf.text('EasyForm AI', margin, y)
  y += 9
  pdf.setFont('helvetica', 'normal')
  pdf.setFontSize(9)
  pdf.text('Simplified guide • Verify requirements with the issuing authority', margin, y)
  y += 12
  writeBlock('Simple explanation', result.simple_explanation)
  resultSections.forEach(({ key, title }) => writeBlock(title, (result[key] || []).map((item) => `• ${item}`).join('\n')))
  writeBlock('Verification note', result.validation?.disclaimer || 'Verify requirements with the issuing authority.')
  pdf.save('easyform-ai-simplified-report.pdf')
}

function Results({ result }) {
  const [copied, setCopied] = useState(false)
  const copyText = async () => {
    const content = [
      'Simple explanation',
      result.simple_explanation,
      ...resultSections.flatMap(({ key, title }) => [`\n${title}`, ...(result[key] || []).map((item) => `• ${item}`)]),
    ].join('\n')
    await navigator.clipboard.writeText(content)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1800)
  }

  return (
    <section className="results-section" id="results" aria-labelledby="results-title">
      <div className="results-heading">
        <div>
          <p className="eyebrow">YOUR PLAIN-LANGUAGE GUIDE</p>
          <h2 id="results-title">Here’s what it means.</h2>
        </div>
        <div className="result-actions">
          <button className="button button-quiet" type="button" onClick={copyText}>
            {copied ? <Check size={16} /> : <Clipboard size={16} />}
            {copied ? 'Copied' : 'Copy all'}
          </button>
          <button className="button button-quiet" type="button" onClick={() => makeReport(result)}>
            <ArrowDownToLine size={16} /> Download PDF
          </button>
        </div>
      </div>

      {result.validation?.flags?.length > 0 && (
        <div className="validation-note" role="status">
          <AlertTriangle size={18} />
          <div>
            <strong>Review highlighted details</strong>
            <p>{result.validation.flags.length} item{result.validation.flags.length === 1 ? '' : 's'} may need checking against the original. Automated checks are not a guarantee of accuracy.</p>
          </div>
        </div>
      )}

      <div className="comparison-grid">
        <article className="comparison-panel original-panel">
          <div className="panel-label"><span className="label-dot dot-slate" /> Original document</div>
          <details>
            <summary>View source text <ChevronDown size={15} /></summary>
            <pre>{result.original_text}</pre>
          </details>
        </article>
        <article className="comparison-panel simple-panel">
          <div className="panel-label"><span className="label-dot dot-green" /> In simple English</div>
          <p>{result.simple_explanation}</p>
        </article>
      </div>

      <div className="result-grid">
        {resultSections.map(({ key, title, marker }) => {
          const items = result[key] || []
          return (
            <article className={`result-card ${items.length ? '' : 'is-empty'}`} key={key}>
              <div className="result-card-top"><span className="result-marker">{marker}</span><span>{items.length}</span></div>
              <h3>{title}</h3>
              {items.length ? (
                <ul>{items.map((item, index) => <li key={`${key}-${index}`}>{item}</li>)}</ul>
              ) : <p className="empty-copy">Nothing specifically mentioned in the text.</p>}
            </article>
          )
        })}
      </div>

      {result.source_sections?.length > 0 && (
        <details className="source-map">
          <summary><FileCheck2 size={16} /> Source-linked sections <ChevronDown size={15} /></summary>
          <p>Each section keeps the source passage beside the AI response that was generated from it.</p>
          {result.source_sections.map((section) => (
            <div className="source-pair" key={section.chunk_number}>
              <div><span>Source {section.chunk_number}</span><p>{section.source_text}</p></div>
              <div><span>Plain-language explanation</span><p>{section.results.simple_explanation || 'See the categories above.'}</p></div>
            </div>
          ))}
        </details>
      )}

      <p className="result-disclaimer"><Info size={15} /> {result.validation?.disclaimer || 'Always confirm official requirements with the relevant government authority.'}</p>
    </section>
  )
}

export default function App() {
  const [mode, setMode] = useState('text')
  const [text, setText] = useState('')
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const fileInput = useRef(null)
  const inputRef = useRef(null)

  const acceptFile = (selectedFile) => {
    setError('')
    if (!selectedFile) return
    if (!selectedFile.name.toLowerCase().endsWith('.pdf') && selectedFile.type !== 'application/pdf') {
      setError('Choose a PDF file to continue.')
      return
    }
    if (selectedFile.size > MAX_FILE_BYTES) {
      setError('This PDF is larger than 15 MB. Choose a smaller file.')
      return
    }
    setFile(selectedFile)
  }

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const response = mode === 'pdf' ? await simplifyPdf(file) : await simplifyText(text)
      setResult(response)
      window.setTimeout(() => document.getElementById('results')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
    } catch (requestError) {
      setError(requestError.message || 'We could not simplify this document. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const clearInput = () => {
    setText('')
    setFile(null)
    setResult(null)
    setError('')
    if (fileInput.current) fileInput.current.value = ''
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href="#home" aria-label="EasyForm AI home">
          <span className="brand-mark"><FileCheck2 size={20} strokeWidth={2.2} /></span>
          <span>easyform<span className="brand-ai">.ai</span></span>
        </a>
        <nav className="main-nav" aria-label="Main navigation">
          <a href="#home">Home</a><a href="#how-it-works">How it works</a><a href="#about">About</a><a href="#privacy">Privacy</a>
        </nav>
        <a className="header-cta" href="#simplify">Get started <ArrowRight size={15} /></a>
      </header>

      <main>
        <section className="hero" id="home">
          <div className="hero-copy">
            <div className="hero-kicker"><span /> LESS PAPERWORK. MORE CLARITY.</div>
            <h1>Government Forms,<br /><span>Made Easy.</span></h1>
            <p>Understand complicated government instructions in simple English with the power of AI.</p>
            <a className="button button-primary hero-button" href="#simplify">Get started <ArrowRight size={17} /></a>
            <div className="hero-proof"><ShieldCheck size={16} /><span>Your documents stay yours. Nothing is stored.</span></div>
          </div>
          <div className="hero-art" aria-hidden="true">
            <div className="orbit orbit-one" /><div className="orbit orbit-two" />
            <div className="paper paper-back"><span /><span /><span /></div>
            <div className="paper paper-front"><div className="paper-top"><FileText size={17} /><span>APPLICATION FORM</span><i>PAGE 01</i></div><b>Instructions for applicants</b><span /><span /><span className="paper-short" /><div className="paper-stamp"><Sparkles size={16} /></div></div>
            <div className="art-note"><span><Check size={13} /></span> The important bits, made clear.</div>
          </div>
        </section>

        <section className="workspace" id="simplify" aria-labelledby="workspace-title">
          <div className="workspace-header">
            <div><p className="eyebrow">START WITH YOUR DOCUMENT</p><h2 id="workspace-title">What do you need help with?</h2></div>
            <div className="privacy-tag"><LockKeyhole size={14} /> Private by design</div>
          </div>

          <form onSubmit={submit}>
            <div className="mode-switch" role="tablist" aria-label="Choose an input type">
              <button type="button" role="tab" aria-selected={mode === 'text'} className={mode === 'text' ? 'active' : ''} onClick={() => { setMode('text'); setError('') }}><Clipboard size={16} /> Paste instructions</button>
              <button type="button" role="tab" aria-selected={mode === 'pdf'} className={mode === 'pdf' ? 'active' : ''} onClick={() => { setMode('pdf'); setError('') }}><FileUp size={16} /> Upload a PDF</button>
            </div>

            {mode === 'text' ? (
              <div className="text-input-wrap">
                <label className="sr-only" htmlFor="instructions">Paste government instructions</label>
                <textarea id="instructions" ref={inputRef} value={text} onChange={(event) => setText(event.target.value)} maxLength={MAX_TEXT_CHARS} placeholder="Paste the form instructions or a section you’d like help understanding…" />
                <div className="input-footer"><span>Include the full section for a more complete explanation.</span><span className={text.length > MAX_TEXT_CHARS * 0.9 ? 'count-near-limit' : ''}>{text.length.toLocaleString()} / {MAX_TEXT_CHARS.toLocaleString()}</span></div>
              </div>
            ) : (
              <div className={`drop-zone ${dragging ? 'is-dragging' : ''} ${file ? 'has-file' : ''}`} onDragOver={(event) => { event.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); acceptFile(event.dataTransfer.files[0]) }}>
                <input ref={fileInput} className="sr-only" type="file" accept="application/pdf,.pdf" onChange={(event) => acceptFile(event.target.files[0])} />
                {file ? (
                  <div className="file-selected"><span className="file-icon"><FileText size={20} /></span><div className="file-meta"><strong>{file.name}</strong><span>{formatBytes(file.size)}</span></div><button className="icon-button" type="button" aria-label="Remove uploaded PDF" title="Remove PDF" onClick={() => { setFile(null); if (fileInput.current) fileInput.current.value = '' }}><X size={17} /></button></div>
                ) : (
                  <div className="drop-content"><span className="upload-icon"><FileUp size={21} /></span><div><strong>Drop your PDF here, or <button className="text-button" type="button" onClick={() => fileInput.current?.click()}>browse files</button></strong><p>PDF only · Up to 15 MB · Text-based PDFs</p></div></div>
                )}
              </div>
            )}

            <div className="input-actions">
              <button className="button button-quiet clear-button" type="button" onClick={clearInput} disabled={!text && !file}><RotateCcw size={15} /> Clear input</button>
              <button className="button button-primary simplify-button" type="submit" disabled={loading || (mode === 'text' ? !text.trim() : !file)}>
                {loading ? <><LoaderCircle className="spin" size={17} /> Reading your document…</> : <><Sparkles size={17} /> Simplify instructions</>}
              </button>
            </div>
            {error && <div className="error-message" role="alert"><AlertTriangle size={17} /><span>{error}</span></div>}
          </form>
          <p className="sensitive-note"><Info size={14} /> Please don’t upload documents containing sensitive personal or confidential information.</p>
        </section>

        {loading && <div className="loading-banner" role="status"><LoaderCircle className="spin" size={19} /><div><strong>Making the details easier to follow</strong><span>Checking each section for dates, fees, and requirements.</span></div></div>}
        {result && <Results result={result} />}

        <section className="how-section" id="how-it-works">
          <div className="section-heading"><p className="eyebrow">A CLEARER WAY FORWARD</p><h2>Three steps to understanding.</h2></div>
          <div className="steps-grid">
            <article><span>01</span><div className="step-icon"><FileUp size={19} /></div><h3>Bring the instructions</h3><p>Paste a section or choose a text-based PDF from your device.</p></article>
            <article><span>02</span><div className="step-icon"><Sparkles size={19} /></div><h3>Let AI untangle it</h3><p>Complex wording is rewritten while key requirements stay visible.</p></article>
            <article><span>03</span><div className="step-icon"><CheckCircle2 size={19} /></div><h3>Review with confidence</h3><p>Compare the plain-language guide with the source before acting.</p></article>
          </div>
        </section>

        <section className="about-strip" id="about">
          <div className="about-icon"><ShieldCheck size={22} /></div>
          <div><p className="eyebrow">BUILT FOR CLARITY</p><h2>Important details should never get lost in the fine print.</h2><p>EasyForm AI helps make public information easier to understand. It is an assistive tool, not a replacement for official guidance or legal advice.</p></div>
        </section>
      </main>

      <footer className="site-footer" id="privacy">
        <div className="footer-main"><a className="brand" href="#home"><span className="brand-mark"><FileCheck2 size={18} /></span><span>easyform<span className="brand-ai">.ai</span></span></a><p>Making government instructions easier to understand, one form at a time.</p></div>
        <div className="footer-notes"><p><LockKeyhole size={14} /> Documents are processed for your request and are not saved by this app.</p><p><Info size={14} /> Always verify requirements, deadlines, and fees with the relevant government authority.</p></div>
        <div className="footer-bottom"><span>EasyForm AI · A student project</span><a href="#privacy">Privacy & responsible use</a></div>
      </footer>
    </div>
  )
}