import React, { useEffect, useRef, useState } from 'react';
import {
  FlaskConical, MessageSquare, FileSearch, Play, Loader2, CheckCircle2, XCircle,
  RotateCcw, Flame, Upload, Download, ChevronDown, ChevronRight, ShieldCheck, Search,
} from 'lucide-react';

const API = 'http://localhost:8000/api';

// Reported in ml/artifacts/nlp_report.md: held-out split of the synthetic data.
const SYNTHETIC_INTENT_ACCURACY = 0.9369;

const REQUIREMENTS = [
  'Offer Letter Signed', 'Govt ID / Passport', 'Direct Deposit Form',
  'Safety Certification', 'Background Check Consent', 'IP Agreement',
];

const pct = (v, digits = 0) => (v == null ? '-' : `${(v * 100).toFixed(digits)}%`);
const label = (s) => (s || '-').replace(/_/g, ' ');

async function call(path, options) {
  const res = await fetch(`${API}${path}`, options);
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

const postJson = (path, body) => call(path, {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}),
});

// ---------------------------------------------------------------------------
// Small building blocks
// ---------------------------------------------------------------------------

const Tick = ({ ok }) => ok
  ? <CheckCircle2 size={16} className="text-status-success shrink-0" />
  : <XCircle size={16} className="text-status-error shrink-0" />;

const Stat = ({ title, value, note, tone }) => (
  <div className="card-nested">
    <p className="text-xs text-text-secondary mb-1">{title}</p>
    <p className={`text-2xl font-serif ${tone === 'good' ? 'text-status-success' : tone === 'bad' ? 'text-status-error' : 'text-accent-gold'}`}>{value}</p>
    {note && <p className="text-xs text-text-secondary mt-1">{note}</p>}
  </div>
);

const Bar = ({ value, highlight }) => (
  <div className="h-2 w-full rounded-full bg-surface-nested overflow-hidden">
    <div className={`h-full rounded-full ${highlight ? 'bg-accent-gold' : 'bg-text-secondary/40'}`}
      style={{ width: `${Math.max(2, (value || 0) * 100)}%` }} />
  </div>
);

const RunButton = ({ onClick, busy, children }) => (
  <button onClick={onClick} disabled={busy} className="btn-primary gap-2 text-sm disabled:opacity-60">
    {busy ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
    {children}
  </button>
);

const Section = ({ step, title, subtitle, action, children }) => (
  <section className="card mb-6">
    <div className="flex flex-col md:flex-row md:items-start justify-between gap-3 mb-5">
      <div>
        {step && <p className="text-xs uppercase tracking-wider text-accent-gold mb-1">{step}</p>}
        <h2 className="text-xl mb-1">{title}</h2>
        {subtitle && <p className="text-sm text-text-secondary max-w-2xl">{subtitle}</p>}
      </div>
      {action}
    </div>
    {children}
  </section>
);

const ErrorNote = ({ error }) => error
  ? <p className="text-sm text-status-error mb-3">Could not reach the backend: {error}</p> : null;

const VerdictPill = ({ verdict }) => {
  const styles = {
    auto_approved: 'bg-status-success/10 text-status-success',
    auto_rejected: 'bg-status-error/10 text-status-error',
    needs_review: 'bg-accent-gold/10 text-accent-gold',
  };
  const names = { auto_approved: 'Approved', auto_rejected: 'Rejected', needs_review: 'Needs HR review' };
  return (
    <span className={`status-pill inline-flex whitespace-nowrap ${styles[verdict] || ''}`}>
      {names[verdict] || label(verdict)}
    </span>
  );
};

// ---------------------------------------------------------------------------
// Chatbot tab
// ---------------------------------------------------------------------------

const MessageProbe = () => {
  const [text, setText] = useState('I still have no laptop and my passport number is K4471902');
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const run = async () => {
    if (!text.trim()) return;
    setBusy(true); setError(null);
    try { setResult(await postJson('/eval/probe/message', { message: text })); }
    catch (e) { setError(e.message); }
    setBusy(false);
  };

  const intents = result ? Object.entries(result.intent_scores).slice(0, 4) : [];

  return (
    <div>
      <div className="flex gap-2 mb-4">
        <input value={text} onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && run()}
          placeholder="Type any message an employee might send"
          className="flex-1 bg-surface-nested border border-subtle rounded-lg px-3 py-2 text-sm outline-none focus:border-accent-hover" />
        <RunButton onClick={run} busy={busy}>Analyse</RunButton>
      </div>
      <ErrorNote error={error} />
      {result && (
        <div className="grid md:grid-cols-3 gap-4">
          <div className="card-nested">
            <p className="text-xs text-text-secondary mb-3">Intent (what they want)</p>
            {intents.map(([name, p], i) => (
              <div key={name} className="mb-2">
                <div className="flex justify-between text-xs mb-1">
                  <span className={i === 0 ? 'text-text-main font-medium' : 'text-text-secondary'}>{label(name)}</span>
                  <span className="text-text-secondary">{pct(p, 1)}</span>
                </div>
                <Bar value={p} highlight={i === 0} />
              </div>
            ))}
          </div>
          <div className="card-nested">
            <p className="text-xs text-text-secondary mb-1">Routed to</p>
            <p className="text-lg font-serif text-accent-gold mb-2">{result.agent}</p>
            <p className="text-xs text-text-secondary">
              {result.routed
                ? `Confidence ${pct(result.intent_confidence)} is above the ${pct(result.confidence_floor)} bar, so it goes straight to this specialist.`
                : `Confidence ${pct(result.intent_confidence)} is below the ${pct(result.confidence_floor)} bar, so the general Onboarding Agent takes it and can hand it on.`}
            </p>
            <p className="text-xs text-text-secondary mt-3">Decided in {result.ms} ms, no language model used.</p>
          </div>
          <div className="card-nested">
            <p className="text-xs text-text-secondary mb-1">Sentiment</p>
            <p className="text-lg font-serif mb-1">{label(result.sentiment)}
              <span className="text-xs font-sans text-text-secondary ml-2">score {result.sentiment_score?.toFixed(2)}</span></p>
            <p className="text-xs text-text-secondary mb-3">At -0.60 or below the message is escalated to HR automatically.</p>
            <p className="text-xs text-text-secondary mb-1">Sent to the language model as</p>
            <p className="text-xs bg-surface-main border border-subtle rounded p-2 break-words">{result.redacted_text}</p>
            {result.redacted_types.length > 0 && (
              <p className="text-xs text-status-success mt-1">Removed: {result.redacted_types.join(', ')}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const RetrievalProbe = () => {
  const [question, setQuestion] = useState('How many days of annual leave do I get?');
  const [empId, setEmpId] = useState('emp_1');
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const run = async (emp = empId) => {
    setBusy(true); setError(null);
    try { setResult(await postJson('/eval/probe/retrieval', { question, emp_id: emp })); }
    catch (e) { setError(e.message); }
    setBusy(false);
  };

  return (
    <div>
      <div className="flex flex-col md:flex-row gap-2 mb-4">
        <select value={empId} onChange={(e) => { setEmpId(e.target.value); run(e.target.value); }}
          className="bg-surface-nested border border-subtle rounded-lg px-3 py-2 text-sm text-text-main">
          <option value="emp_1">Shreya, Nimbus Labs</option>
          <option value="emp_2">Adithya, Veltrix Corp</option>
        </select>
        <input value={question} onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && run()}
          className="flex-1 bg-surface-nested border border-subtle rounded-lg px-3 py-2 text-sm outline-none focus:border-accent-hover" />
        <RunButton onClick={() => run()} busy={busy}>Search</RunButton>
      </div>
      <ErrorNote error={error} />
      {result && (
        result.results.length === 0
          ? <p className="text-sm text-text-secondary">Nothing in {result.org}'s handbook matches. The assistant is told to say so and offer HR, not to guess.</p>
          : <div className="space-y-2">
            {result.results.map((r, i) => {
              const strong = r.score >= result.weak_match_score;
              return (
                <div key={i} className="card-nested">
                  <div className="flex justify-between items-center gap-3 mb-1">
                    <p className="text-sm font-medium">{r.doc_title} <span className="text-text-secondary">/ {r.section}</span></p>
                    <span className={`text-xs whitespace-nowrap ${strong ? 'text-status-success' : 'text-accent-gold'}`}>
                      {r.score.toFixed(2)} {strong ? 'strong' : 'weak'}
                    </span>
                  </div>
                  <p className="text-xs text-text-secondary">{r.text.split('\n').slice(1).join(' ').slice(0, 220)}</p>
                </div>
              );
            })}
            <p className="text-xs text-text-secondary">Searching {result.org} only. Scores below {result.weak_match_score} count as "not really an answer".</p>
          </div>
      )}
    </div>
  );
};

const RoutingBenchmark = () => {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [missesOnly, setMissesOnly] = useState(false);

  const run = async () => {
    setBusy(true); setError(null);
    try { setData(await call('/eval/routing')); } catch (e) { setError(e.message); }
    setBusy(false);
  };

  const rows = data ? data.rows.filter(r => !missesOnly || !r.intent_correct) : [];

  return (
    <Section step="Layer 1" title="Routing: does each message reach the right specialist?"
      subtitle="48 messages written by hand in natural wording, 6 per intent. None of them came from the training generator."
      action={<RunButton onClick={run} busy={busy}>Run 48 messages</RunButton>}>
      <ErrorNote error={error} />
      {data && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
            <Stat title="Intent accuracy, hand-written" value={pct(data.intent_accuracy)}
              note={`${data.rows.filter(r => r.intent_correct).length} of ${data.n} correct`} />
            <Stat title="Intent accuracy, synthetic test set" value={pct(SYNTHETIC_INTENT_ACCURACY)}
              note="Same model, data shaped like its training set" />
            <Stat title="Sentiment accuracy" value={pct(data.sentiment_accuracy)} note="3 classes" />
            <Stat title="Time per message" value={`${data.mean_ms.toFixed(0)} ms`} note="Classifier only" />
          </div>
          <p className="text-sm text-text-secondary mb-5">
            The gap between the two accuracy figures is the main finding here. The model learned from templated
            messages, so natural wording costs about {Math.round((SYNTHETIC_INTENT_ACCURACY - data.intent_accuracy) * 100)} points.
            A misrouted message is not lost: every specialist can hand the conversation to the right one.
          </p>
          <div className="grid md:grid-cols-4 gap-3 mb-5">
            {Object.entries(data.per_intent).map(([intent, v]) => (
              <div key={intent}>
                <div className="flex justify-between text-xs mb-1">
                  <span>{label(intent)}</span><span className="text-text-secondary">{v.correct}/{v.n}</span>
                </div>
                <Bar value={v.correct / v.n} highlight />
              </div>
            ))}
          </div>
          <label className="flex items-center gap-2 text-sm text-text-secondary mb-3 cursor-pointer">
            <input type="checkbox" checked={missesOnly} onChange={(e) => setMissesOnly(e.target.checked)} />
            Show misses only
          </label>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-text-secondary border-b border-subtle">
                <th className="py-2 pr-2"></th><th className="py-2 pr-4">Message</th>
                <th className="py-2 pr-4">Expected</th><th className="py-2 pr-4">Predicted</th>
                <th className="py-2 pr-4">Specialist</th><th className="py-2">Sentiment</th>
              </tr></thead>
              <tbody>
                {rows.map(r => (
                  <tr key={r.id} className="border-b border-subtle/60 align-top">
                    <td className="py-2 pr-2"><Tick ok={r.intent_correct} /></td>
                    <td className="py-2 pr-4">{r.message}</td>
                    <td className="py-2 pr-4 text-text-secondary whitespace-nowrap">{label(r.expected_intent)}</td>
                    <td className="py-2 pr-4 whitespace-nowrap">{label(r.predicted_intent)}
                      <span className="text-xs text-text-secondary ml-1">{pct(r.intent_confidence)}</span></td>
                    <td className="py-2 pr-4 text-text-secondary whitespace-nowrap">{r.routed_agent}</td>
                    <td className={`py-2 whitespace-nowrap ${r.sentiment_correct ? 'text-text-secondary' : 'text-status-error'}`}>
                      {label(r.predicted_sentiment)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Section>
  );
};

const RetrievalBenchmark = () => {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const run = async () => {
    setBusy(true); setError(null);
    try { setData(await call('/eval/retrieval')); } catch (e) { setError(e.message); }
    setBusy(false);
  };

  const kindName = { answer: 'Has an answer', no_answer: 'Not in handbook', isolation: 'Other company only' };

  return (
    <Section step="Layer 2" title="Policy search: does it find the right passage, and only this company's?"
      subtitle="16 questions: 12 the handbook answers, 2 it does not, and 2 that only the other company's handbook answers, which must never be shown."
      action={<RunButton onClick={run} busy={busy}>Run 16 questions</RunButton>}>
      <ErrorNote error={error} />
      {data && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
            <Stat title="Right section ranked first" value={pct(data.hit_at_1)} />
            <Stat title="Right section in top 3" value={pct(data.hit_at_3)} note="The assistant reads the top 3" />
            <Stat title="Correctly finds nothing" value={`${data.declines_correct}/${data.declines_total}`}
              tone={data.declines_correct === data.declines_total ? 'good' : 'bad'} />
            <Stat title="No leaks between companies" value={`${data.isolation_correct}/${data.isolation_total}`}
              tone={data.isolation_correct === data.isolation_total ? 'good' : 'bad'} />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-text-secondary border-b border-subtle">
                <th className="py-2 pr-2"></th><th className="py-2 pr-4">Question</th><th className="py-2 pr-4">Asked by</th>
                <th className="py-2 pr-4">Type</th><th className="py-2 pr-4">Top result</th><th className="py-2">Result</th>
              </tr></thead>
              <tbody>
                {data.rows.map(r => (
                  <tr key={r.id} className="border-b border-subtle/60 align-top">
                    <td className="py-2 pr-2"><Tick ok={r.passed} /></td>
                    <td className="py-2 pr-4">{r.question}</td>
                    <td className="py-2 pr-4 text-text-secondary whitespace-nowrap">{r.org}</td>
                    <td className="py-2 pr-4 text-text-secondary whitespace-nowrap">{kindName[r.kind]}</td>
                    <td className="py-2 pr-4 text-text-secondary">
                      {r.results[0] ? `${r.results[0].section} (${r.results[0].score})` : 'nothing'}</td>
                    <td className="py-2 text-text-secondary text-xs">{r.detail}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Section>
  );
};

const AnswerBenchmark = () => {
  const [summary, setSummary] = useState(null);
  const [running, setRunning] = useState(null);
  const [open, setOpen] = useState({});
  const [error, setError] = useState(null);
  const stopRef = useRef(false);

  const load = async () => {
    try { setSummary(await call('/eval/answers')); } catch (e) { setError(e.message); }
  };
  useEffect(() => { load(); }, []);

  const runOne = async (id) => {
    setRunning(id); setError(null);
    try { await call(`/eval/answers/${id}`, { method: 'POST' }); setOpen(o => ({ ...o, [id]: true })); }
    catch (e) { setError(e.message); }
    await load();
    setRunning(null);
  };

  const runAll = async () => {
    stopRef.current = false;
    for (const c of summary.cases) {
      if (stopRef.current) break;
      await runOne(c.id);
    }
  };

  const byId = Object.fromEntries((summary?.rows || []).map(r => [r.id, r]));

  return (
    <Section step="Layer 3" title="Full answers: is the reply correct, cited, and honest?"
      subtitle={`The whole assistant: router, specialist agent, policy search and the language model (${summary?.model || '...'} running locally). Each reply takes about 20 to 45 seconds on this laptop, so results are saved and the last run is shown.`}
      action={
        <div className="flex gap-2">
          {running
            ? <button onClick={() => { stopRef.current = true; }} className="btn-secondary text-sm">Stop after this one</button>
            : <RunButton onClick={runAll} busy={false}>Run all 16</RunButton>}
        </div>
      }>
      <ErrorNote error={error} />
      {summary && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
            <Stat title="Answers that pass" value={pct(summary.pass_rate)}
              note={`${summary.rows.filter(r => r.passed).length} of ${summary.n} run`} />
            <Stat title="Correct fact" value={`${summary.fact_correct?.passed ?? '-'}/${summary.fact_correct?.total ?? '-'}`}
              note={`Cited the section: ${summary.cited?.passed ?? '-'}/${summary.cited?.total ?? '-'}`} />
            <Stat title="Declines when it should" value={`${summary.declined?.passed ?? '-'}/${summary.declined?.total ?? '-'}`}
              note="No answer in handbook, or other company only" />
            <Stat title="Average reply time" value={summary.mean_seconds ? `${summary.mean_seconds.toFixed(1)} s` : '-'}
              note={summary.updated_at ? `On this laptop · last run ${summary.updated_at.slice(11, 16)}` : 'On this laptop'} />
          </div>
          <div className="space-y-2">
            {summary.cases.map(c => {
              const r = byId[c.id];
              const isOpen = open[c.id];
              return (
                <div key={c.id} className="card-nested">
                  <div className="flex items-center gap-3">
                    <button onClick={() => setOpen(o => ({ ...o, [c.id]: !o[c.id] }))} className="text-text-secondary"
                      disabled={!r}>{isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}</button>
                    {r ? <Tick ok={r.passed} /> : <span className="w-4" />}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm truncate">{c.question}</p>
                      <p className="text-xs text-text-secondary">{c.org} · {c.kind === 'answer' ? 'should answer with a citation' : 'should decline'}
                        {r && ` · ${r.specialist}${r.transferred_from ? ` (handed on from ${r.transferred_from})` : ''} · ${r.seconds}s`}</p>
                    </div>
                    <button onClick={() => runOne(c.id)} disabled={!!running}
                      className="btn-secondary text-xs gap-1 py-1 disabled:opacity-50">
                      {running === c.id ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
                      {running === c.id ? 'Thinking' : 'Run'}
                    </button>
                  </div>
                  {r && isOpen && (
                    <div className="mt-3 ml-11">
                      <p className="text-sm bg-surface-main border border-subtle rounded p-3 whitespace-pre-wrap mb-2">{r.response}</p>
                      <div className="flex flex-wrap gap-3">
                        {r.checks.map(ch => (
                          <span key={ch.check} className="flex items-center gap-1 text-xs text-text-secondary" title={ch.detail}>
                            <Tick ok={ch.passed} />{ch.check}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </Section>
  );
};

const ChatbotTab = () => (
  <>
    <Section title="Try any message" subtitle="Type something an employee might say. This shows what the classifiers decide before the language model is called.">
      <MessageProbe />
    </Section>
    <Section title="Try any policy question" subtitle="Search one company's handbook. Switch the employee to see the same question answered from a different handbook.">
      <RetrievalProbe />
    </Section>
    <RoutingBenchmark />
    <RetrievalBenchmark />
    <AnswerBenchmark />
  </>
);

// ---------------------------------------------------------------------------
// Document tab
// ---------------------------------------------------------------------------

const AnalysisCard = ({ a }) => {
  const topTypes = Object.entries(a.type_scores || {}).sort((x, y) => y[1] - x[1]).slice(0, 3);
  const f = a.extracted_fields || {};
  return (
    <div className="grid md:grid-cols-3 gap-4">
      <div className="card-nested">
        <p className="text-xs text-text-secondary mb-2">Verdict</p>
        <VerdictPill verdict={a.verdict} />
        <p className="text-sm mt-3">{a.reason}</p>
        <p className="text-xs text-text-secondary mt-3">Read via {a.extraction?.method} in {a.ms} ms</p>
      </div>
      <div className="card-nested">
        <p className="text-xs text-text-secondary mb-3">Document type</p>
        {topTypes.length === 0 && <p className="text-sm text-text-secondary">No text to classify.</p>}
        {topTypes.map(([name, p], i) => (
          <div key={name} className="mb-2">
            <div className="flex justify-between text-xs mb-1">
              <span className={i === 0 ? 'font-medium' : 'text-text-secondary'}>{label(name)}</span>
              <span className="text-text-secondary">{pct(p, 1)}</span>
            </div>
            <Bar value={p} highlight={i === 0} />
          </div>
        ))}
        <p className="text-xs text-text-secondary mt-3">
          Names: {(f.names || []).join(', ') || 'none'}<br />
          Expiry: {f.dates?.expiry || 'none'} · Signature: {f.signature_state || (f.has_signature ? 'signed' : 'absent')}
        </p>
      </div>
      <div className="card-nested">
        <p className="text-xs text-text-secondary mb-3">Checks</p>
        <ul className="space-y-2">
          {(a.checks || []).map((c, i) => (
            <li key={i} className="flex gap-2 text-xs">
              <Tick ok={c.passed && c.severity !== 'warning'} />
              <span><span className="font-medium">{label(c.check)}</span>
                <span className="text-text-secondary"> ({c.severity})</span><br />
                <span className="text-text-secondary">{c.message}</span></span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

const DocumentProbe = () => {
  const [file, setFile] = useState(null);
  const [requirement, setRequirement] = useState('Offer Letter Signed');
  const [employee, setEmployee] = useState('Shreya Nair');
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const run = async () => {
    if (!file) return;
    setBusy(true); setError(null);
    const form = new FormData();
    form.append('file', file);
    if (requirement) form.append('requirement', requirement);
    if (employee) form.append('employee_name', employee);
    try { setResult(await call('/eval/probe/document', { method: 'POST', body: form })); }
    catch (e) { setError(e.message); }
    setBusy(false);
  };

  return (
    <div>
      <div className="grid md:grid-cols-4 gap-2 mb-4">
        <label className="btn-secondary text-sm gap-2 cursor-pointer truncate">
          <Upload size={16} /> <span className="truncate">{file ? file.name : 'Choose a PDF or image'}</span>
          <input type="file" accept=".pdf,image/*" className="hidden"
            onChange={(e) => { setFile(e.target.files[0] || null); setResult(null); }} />
        </label>
        <select value={requirement} onChange={(e) => setRequirement(e.target.value)}
          className="bg-surface-nested border border-subtle rounded-lg px-3 py-2 text-sm text-text-main">
          <option value="">No requirement (just classify)</option>
          {REQUIREMENTS.map(r => <option key={r} value={r}>Uploaded as: {r}</option>)}
        </select>
        <input value={employee} onChange={(e) => setEmployee(e.target.value)} placeholder="Employee name"
          className="bg-surface-nested border border-subtle rounded-lg px-3 py-2 text-sm outline-none" />
        <RunButton onClick={run} busy={busy}>Verify</RunButton>
      </div>
      <ErrorNote error={error} />
      {result && <AnalysisCard a={result} />}
    </div>
  );
};

const DocumentBenchmark = () => {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [open, setOpen] = useState({});

  const run = async () => {
    setBusy(true); setError(null);
    try { setData(await call('/eval/documents')); } catch (e) { setError(e.message); }
    setBusy(false);
  };

  const names = { auto_approved: 'Approved', needs_review: 'Review', auto_rejected: 'Rejected' };

  return (
    <Section step="Benchmark" title="16 documents, each with the verdict a careful HR officer would give"
      subtitle="Signed and unsigned, valid and expired, the wrong person, the wrong document, a damaged scan and a photo. Dates are worked out from today, so 'expires in 10 days' is always true."
      action={<RunButton onClick={run} busy={busy}>Verify 16 documents</RunButton>}>
      <ErrorNote error={error} />
      {data && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
            <Stat title="Correct verdict" value={pct(data.accuracy)} note={`${data.rows.filter(r => r.passed).length} of ${data.n}`} />
            <Stat title="Bad documents approved" value={data.wrongly_approved.length}
              tone={data.wrongly_approved.length === 0 ? 'good' : 'bad'} note="The mistake that matters most" />
            <Stat title="Time per document" value={`${data.mean_ms.toFixed(0)} ms`} />
            <div className="card-nested">
              <p className="text-xs text-text-secondary mb-2">Expected (rows) vs given (columns)</p>
              <table className="text-xs w-full">
                <thead><tr><th></th>{data.confusion.labels.map(l => <th key={l} className="font-normal text-text-secondary">{names[l]}</th>)}</tr></thead>
                <tbody>{data.confusion.labels.map(e => (
                  <tr key={e}><td className="text-text-secondary pr-1">{names[e]}</td>
                    {data.confusion.labels.map(p => {
                      const n = data.confusion.matrix[e][p];
                      return <td key={p} className={`text-center ${n && e === p ? 'text-status-success font-medium' : n ? 'text-status-error font-medium' : 'text-text-secondary/50'}`}>{n}</td>;
                    })}</tr>
                ))}</tbody>
              </table>
            </div>
          </div>
          <div className="space-y-2">
            {data.rows.map(r => (
              <div key={r.id} className="card-nested">
                <div className="flex flex-col md:flex-row md:items-center gap-3">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <button onClick={() => setOpen(o => ({ ...o, [r.id]: !o[r.id] }))} className="text-text-secondary">
                      {open[r.id] ? <ChevronDown size={16} /> : <ChevronRight size={16} />}</button>
                    <Tick ok={r.passed} />
                    <div className="min-w-0">
                      <p className="text-sm">{r.title}</p>
                      <p className="text-xs text-text-secondary">{r.employee}, uploaded as "{r.requirement}" · {r.teaches}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 ml-11 md:ml-0">
                    <span className="text-xs text-text-secondary">expected</span><VerdictPill verdict={r.expected} />
                    <span className="text-xs text-text-secondary">got</span><VerdictPill verdict={r.verdict} />
                    <a href={`${API}/eval/documents/${encodeURIComponent(r.file)}`} className="text-text-secondary hover:text-text-main" title="Download this file">
                      <Download size={16} /></a>
                  </div>
                </div>
                {open[r.id] && (
                  <div className="mt-3 ml-11 text-xs">
                    <p className="mb-2"><span className="text-text-secondary">Reason:</span> {r.reason}</p>
                    <p className="mb-2 text-text-secondary">Classified as {label(r.predicted_type)} ({pct(r.confidence)}) ·
                      names {r.fields.names.join(', ') || 'none'} · expiry {r.fields.expiry || 'none'} · signature {r.fields.signature}</p>
                    <ul className="space-y-1">
                      {r.checks.map((c, i) => (
                        <li key={i} className="flex gap-2"><Tick ok={c.passed && c.severity !== 'warning'} />
                          <span>{label(c.check)}: <span className="text-text-secondary">{c.message}</span></span></li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </Section>
  );
};

const DocumentsTab = () => (
  <>
    <Section title="Try any document" subtitle="Upload any PDF or image and choose what it is supposed to be. Nothing is saved to an employee record.">
      <DocumentProbe />
    </Section>
    <DocumentBenchmark />
  </>
);

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export const EvaluationLab = () => {
  const [tab, setTab] = useState('chat');
  const [warm, setWarm] = useState(null);
  const [resetState, setResetState] = useState(null);

  const warmUp = async () => {
    setWarm({ busy: true });
    try { setWarm(await postJson('/eval/warmup')); } catch (e) { setWarm({ ok: false, detail: e.message }); }
  };

  const reset = async () => {
    if (!window.confirm('Reset every employee to the starting demo state and clear all chats and uploads?')) return;
    setResetState('busy');
    try { await postJson('/eval/reset-demo'); setResetState('done'); window.location.reload(); }
    catch { setResetState('failed'); }
  };

  return (
    <div className="animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between md:items-end gap-4 mb-6">
        <div>
          <h1 className="text-3xl mb-1 flex items-center gap-3"><FlaskConical className="text-accent-gold" /> Evaluation Lab</h1>
          <p className="text-text-secondary max-w-2xl">
            Every test case here was written by hand after the models were trained, in wording the training
            data never used. Run them live and judge for yourself.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <button onClick={warmUp} disabled={warm?.busy} className="btn-secondary text-sm gap-2">
            {warm?.busy ? <Loader2 size={16} className="animate-spin" /> : <Flame size={16} />}
            {warm?.busy ? 'Loading model' : warm?.ok ? `Model ready (${warm.seconds}s)` : 'Warm up model'}
          </button>
          <button onClick={reset} disabled={resetState === 'busy'} className="btn-secondary text-sm gap-2">
            <RotateCcw size={16} /> Reset demo data
          </button>
        </div>
      </div>
      {warm && warm.ok === false && <p className="text-sm text-status-error mb-4">Model not reachable: {warm.detail}</p>}

      <div className="flex gap-1 bg-surface-nested border border-subtle p-1 rounded-lg w-fit mb-6">
        {[['chat', 'Chatbot', MessageSquare], ['docs', 'Document verification', FileSearch]].map(([key, name, Icon]) => (
          <button key={key} onClick={() => setTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm transition-colors ${tab === key ? 'bg-surface-main text-text-main shadow-sm' : 'text-text-secondary hover:text-text-main'}`}>
            <Icon size={16} /> {name}
          </button>
        ))}
      </div>

      {tab === 'chat' ? <ChatbotTab /> : <DocumentsTab />}

      <p className="text-xs text-text-secondary flex items-center gap-2 mt-2 mb-8">
        <ShieldCheck size={14} /> Test cases live in backend/evaluation. <Search size={14} /> The same run can be produced offline with: python -m evaluation.report
      </p>
    </div>
  );
};
