import { useEffect, useRef, useState, type FormEvent } from "react";
import { ApiError, askAssistant, getAssistantStatus, type AssistantReply, type AssistantSource, type AssistantStatus } from "./api";
import { savedDuration } from "./savedTime";

const labels: Record<string, string> = {
  get_day_plan: "Day plan", get_week_plan: "Week plan", search_tasks: "Task search",
  get_task: "Task details", get_time_summary: "Saved time and completion",
};

function Source({ source }: { source: AssistantSource }) {
  const data = source.data;
  const items = (data.items ?? data.tasks ?? (data.task ? [data.task] : [])) as Record<string, unknown>[];
  return <details className="assistant-source" open>
    <summary>{labels[source.tool] ?? "Saved records"}</summary>
    {typeof data.active_microseconds === "number" ? <>
      <p><strong>All-time saved active time: {savedDuration(data.active_microseconds)}</strong></p>
      <p>{String(data.session_count)} saved sessions · {String(data.timezone)}</p>
      <p>Current leaf completion: {String((data.completion as Record<string, unknown>).completed)} of {String((data.completion as Record<string, unknown>).total)}</p>
      <ul>{(data.days as Record<string, unknown>[]).map((day) => <li key={String(day.date)}>{String(day.date)}: {savedDuration(day.active_microseconds as number)}</li>)}</ul>
      {data.days_truncated ? <p>Showing the latest 31 dates; the total includes all saved dates.</p> : null}
    </> : <>
      {source.tool === "search_tasks" ? <p>Search scope: {data.scope_project_name ? String(data.scope_project_name) : "All projects"}</p> : null}
      {data.start_date ? <p>{String(data.start_date)}{data.end_date !== data.start_date ? ` – ${String(data.end_date)}` : ""} · {String(data.timezone)} · {data.historical ? "Frozen history" : "Current plan"}</p> : null}
      {typeof data.unique_leaf_total === "number" ? <p>{String(data.completed_leaf_total)} of {data.unique_leaf_total} unique planned work items complete</p> : null}
      <ul>{items.map((item, index) => <li key={`${String(item.task_id ?? item.id)}-${index}`}>
        <strong>{String(item.title)}</strong>
        <p>{String(item.project_name ?? "")}{item.parent_title ? ` / ${String(item.parent_title)}` : ""}</p>
        <p>{item.completed ? "Complete" : "Incomplete"}{item.planned_date ? ` · Planned ${String(item.planned_date)}` : ""} · Due {item.deadline ? String(item.deadline) : "not set"}</p>
        {item.notes ? <p>{String(item.notes)}{item.notes_truncated ? " (excerpt)" : ""}</p> : null}
      </li>)}</ul>
      {!items.length ? <p>No matching planned work or tasks.</p> : null}
      {data.truncated || data.next_offset != null ? <p>More records exist. Narrow your question or ask for the next page.</p> : null}
      {typeof data.total === "number" ? <p>{data.total} matches · Showing {items.length} from offset {String(data.offset)}</p> : null}
    </>}
  </details>;
}

export function Assistant({ visible, projectId, date }: { visible: boolean; projectId: string | null; date?: string }) {
  const [status, setStatus] = useState<AssistantStatus | null>(null);
  const [model, setModel] = useState("");
  const [prompt, setPrompt] = useState("");
  const [reply, setReply] = useState<AssistantReply | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const request = useRef<AbortController | null>(null);
  const statusRequest = useRef<AbortController | null>(null);

  async function refresh() {
    statusRequest.current?.abort();
    const controller = new AbortController();
    statusRequest.current = controller;
    setLoading(true); setError(null);
    try {
      const loaded = await getAssistantStatus(controller.signal);
      if (controller.signal.aborted) return;
      setStatus(loaded);
      setModel((current) => loaded.models.some((m) => m.name === current) ? current
        : loaded.models.find((m) => m.name === "qwen3:8b")?.name
          ?? loaded.models.find((m) => m.name === "qwen3:4b")?.name ?? "");
    } catch (caught) {
      if (!controller.signal.aborted) { setStatus(null); setError(caught instanceof ApiError ? caught.message : "Could not reach the local assistant. Refresh models to retry."); }
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }

  function cancel() {
    request.current?.abort();
    setBusy(false);
  }

  useEffect(() => {
    if (visible) void refresh();
    return () => { request.current?.abort(); statusRequest.current?.abort(); };
  }, [visible]);

  useEffect(() => { if (!visible) { setBusy(false); setLoading(false); } }, [visible]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (busy || !model || !prompt.trim()) return;
    const controller = new AbortController();
    request.current = controller;
    setBusy(true); setError(null); setReply(null);
    try {
      const result = await askAssistant(model, prompt.trim(), { project_id: projectId, date: date ?? null }, controller.signal);
      if (!controller.signal.aborted) setReply(result);
    } catch (caught) {
      if (!controller.signal.aborted) setError(caught instanceof ApiError ? caught.message : "The question could not finish. Your input is kept; try again.");
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }

  return <section hidden={!visible} className="assistant" aria-label="Local assistant">
    <div className="forest-heading"><h2>Local assistant</h2><button type="button" className="link" disabled={loading || busy} onClick={() => void refresh()}>Refresh models</button></div>
    <p className="muted">Ask about your plans, tasks and saved time. This version can read records. Use Plan and Track to make changes.</p>
    {loading ? <p role="status">Checking local models…</p> : null}
    {error ? <p role="alert" className="error">{error}</p> : null}
    {status && !status.models.length ? <p>No local models are installed. Add a tools-capable model in Ollama, then refresh. BearPlans does not download models automatically.</p> : null}
    <form onSubmit={(event) => void submit(event)} className="assistant-form">
      <label htmlFor="assistant-model">Local model</label>
      <select id="assistant-model" value={model} disabled={busy || loading || !status} onChange={(event) => setModel(event.target.value)}>
        <option value="">Choose a local tools-capable model</option>
        {status?.models.map((item) => <option key={item.name} value={item.name}>{item.name}</option>)}
      </select>
      <label htmlFor="assistant-question">Question</label>
      <textarea id="assistant-question" rows={4} maxLength={2000} disabled={busy} value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="What is planned today? How much work have I saved?" />
      <p className="muted">Uses your selected project and week as context. Each question is independent. Questions and replies stay in this page until you reload.</p>
      <div className="form-actions"><button type="submit" disabled={!status || !model || !prompt.trim() || busy || loading}>{busy ? "Looking up…" : "Ask"}</button>
        {busy ? <button type="button" onClick={cancel}>Cancel question</button> : null}</div>
    </form>
    {busy ? <p role="status">Reading saved records… You can still use Plan, Track and Stats.</p> : null}
    {reply ? <div className="assistant-reply" aria-live="polite">
      <h3>Model reply</h3><p className="assistant-answer">{reply.answer}</p>
      <p className="muted">{reply.model} · {reply.elapsed_seconds} s · Read only</p>
      <h3>Saved records used</h3><p className="muted">These values come directly from BearPlans. Check them when a model's wording is unclear.</p>
      {reply.sources.length ? reply.sources.map((source, index) => <Source key={index} source={source} />) : <p>No saved records were read for this reply.</p>}
    </div> : null}
  </section>;
}
