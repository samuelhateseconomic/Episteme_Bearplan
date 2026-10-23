import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { ApiError, applyCorrection, getSavedSessions, previewCorrection, type CorrectionDraft, type CorrectionPreview, type PendingCorrection, type SavedSession } from "./api";
import { savedDuration } from "./savedTime";

const STORAGE = "bearplans-pending-correction-v1:";
const signed = (value: number) => `${value > 0 ? "+" : ""}${value}`;
const message = (error: unknown) => error instanceof ApiError ? error.message : "Could not complete this request. Try again.";

function restorePending(): PendingCorrection | null {
  try {
    for (const key of Object.keys(localStorage).filter((key) => key.startsWith(STORAGE)).sort()) {
      let value: PendingCorrection | null;
      try { value = JSON.parse(localStorage.getItem(key) ?? "null") as PendingCorrection | null; } catch { continue; }
      if (value && typeof value.session_id === "string" && typeof value.operation_id === "string" && typeof value.preview_token === "string"
        && typeof value.draft?.reason === "string" && Number.isInteger(value.draft?.expected_revision) && Array.isArray(value.draft?.intervals)
        && value.draft.intervals.every((row) => typeof row?.id === "string" && Number.isSafeInteger(row.active_microseconds))) return value;
    }
    return null;
  } catch { return null; }
}

// Decimal parsing avoids binary rounding silently changing a microsecond.
function parseSeconds(value: string): number {
  if (!/^\d+(?:\.\d{1,6})?$/.test(value)) throw new Error("Use nonnegative seconds with at most six decimal places.");
  const [whole, fraction = ""] = value.split(".");
  const result = Number(whole) * 1_000_000 + Number(fraction.padEnd(6, "0"));
  if (!Number.isSafeInteger(result)) throw new Error("This duration is too large.");
  return result;
}

export function Corrections({ visible, onApplied }: { visible: boolean; onApplied: () => void }) {
  const [sessions, setSessions] = useState<SavedSession[] | null>(null);
  const [selected, setSelected] = useState<SavedSession | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [reason, setReason] = useState("");
  const [review, setReview] = useState<{ draft: CorrectionDraft; preview: CorrectionPreview } | null>(null);
  const [pending, setPending] = useState<PendingCorrection | null>(restorePending);
  const [rejected, setRejected] = useState<PendingCorrection | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const request = useRef<AbortController | null>(null);
  const visibleRef = useRef(visible);
  visibleRef.current = visible;
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);

  const refresh = useCallback(async () => {
    if (!visibleRef.current) return;
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setLoading(true);
    try {
      const loaded = await getSavedSessions(controller.signal);
      if (!controller.signal.aborted) {
        setSessions(loaded); setError(null); setReview(null);
        setSelected((current) => current ? loaded.find((session) => session.id === current.id) ?? null : null);
      }
    } catch (caught) {
      if (!controller.signal.aborted) setError(caught instanceof ApiError && caught.status === 404
        ? "Saved session corrections need the updated local service. Restart BearPlans, then refresh saved sessions." : message(caught));
    } finally { if (!controller.signal.aborted) setLoading(false); }
  }, []);
  useEffect(() => {
    if (visible) void refresh();
    return () => request.current?.abort();
  }, [visible, refresh]);
  useEffect(() => {
    if (!rejected || !sessions) return;
    const session = sessions.find((row) => row.id === rejected.session_id);
    if (!session) return;
    setSelected(session);
    setValues(Object.fromEntries(rejected.draft.intervals.map((row) => [row.id, String(row.active_microseconds / 1_000_000)])));
    setReason(rejected.draft.reason);
    setRejected(null);
  }, [rejected, sessions]);

  function edit(session: SavedSession, reverse = false) {
    setSelected(session); setReview(null); setError(null); setStatus("");
    const intervals = reverse ? session.history[0].before : session.intervals;
    setValues(Object.fromEntries(intervals.map((row) => [row.id, String(row.active_microseconds / 1_000_000)])));
    setReason(reverse ? `Reversal of correction ${session.history[0].operation_id}` : "");
  }

  async function preview(event: FormEvent) {
    event.preventDefault();
    if (!selected) return;
    setError(null); setBusy(true); setReview(null);
    try {
      const draft: CorrectionDraft = { expected_revision: selected.revision, reason,
        intervals: selected.intervals.map((row) => ({ id: row.id, active_microseconds: parseSeconds(values[row.id] ?? "") })) };
      const loaded = await previewCorrection(selected.id, draft);
      if (mounted.current) setReview({ draft, preview: loaded });
    } catch (caught) { if (mounted.current) setError(caught instanceof Error ? caught.message : message(caught)); }
    finally { if (mounted.current) setBusy(false); }
  }

  async function save(packet: PendingCorrection) {
    setBusy(true); setError(null);
    try {
      const result = await applyCorrection(packet);
      localStorage.removeItem(STORAGE + packet.operation_id);
      onApplied();
      if (mounted.current) {
        setPending(restorePending()); setReview(null); setSelected(null);
        setStatus(`Correction saved. This request recorded ${savedDuration(result.active_microseconds)}. Coin adjustment: ${signed(result.coin_delta)}. Refreshed reports show the current saved state.`);
        await refresh();
      }
    } catch (caught) {
      if (!mounted.current) return;
      // Definite validation/conflict rejection made no change; a new preview is safe.
      // Unknown/network/storage outcomes retain the exact operation until retried.
      if (caught instanceof ApiError && (caught.status === 409 || caught.status === 422)) {
        localStorage.removeItem(STORAGE + packet.operation_id); setPending(restorePending()); setReview(null);
        setRejected(packet);
      }
      setError(message(caught));
    } finally { if (mounted.current) setBusy(false); }
  }

  function applyReviewed() {
    if (!review || !selected) return;
    const packet: PendingCorrection = { session_id: selected.id, draft: review.draft, preview_token: review.preview.preview_token, operation_id: crypto.randomUUID() };
    try { localStorage.setItem(STORAGE + packet.operation_id, JSON.stringify(packet)); }
    catch { setError("The retry request could not be saved in this browser. Allow local storage, then apply again."); return; }
    setPending(packet);
    void save(packet);
  }

  return <section hidden={!visible} className="session-corrections" aria-label="Saved session corrections">
    <div className="forest-heading"><h3>Saved session corrections</h3>
      <button type="button" className="link" disabled={busy || loading} onClick={() => void refresh()}>Refresh saved sessions</button></div>
    <p className="muted">Correct recorded active time or restore previously reduced time, up to each interval's original confirmed maximum. Dates and gaps stay fixed. Review changes before applying; the audit is permanent. Purchases stay yours if your coin balance becomes negative; new purchases wait until it recovers.</p>
    {loading ? <p role="status">Loading saved sessions…</p> : null}
    {error ? <p role="alert" className="error">{error} Your inputs are kept. Refresh saved sessions to review current records.</p> : null}
    {status ? <p role="status">{status}</p> : null}
    {pending ? <div className="correction-review" role="region" aria-label="Pending correction">
      <p>A correction request is awaiting a confirmed response. Retry this exact request to check its saved result, including after reload.</p>
      <button type="button" disabled={busy} onClick={() => void save(pending)}>Retry correction</button>
    </div> : null}
    {!pending && selected ? <form onSubmit={(event) => void preview(event)} aria-label="Edit saved session">
      <h4>{selected.project_name} / {selected.task_title}</h4>
      <fieldset disabled={busy || Boolean(review)}><legend>Saved active intervals</legend>
        {selected.intervals.map((row, index) => <label className="correction-interval" key={row.id}>
          Interval {index + 1} active seconds
          <span className="muted">{row.started_at} → {row.ended_at} · Original maximum: {savedDuration(row.maximum_microseconds)}</span>
          <input type="text" inputMode="decimal" required value={values[row.id] ?? ""} onChange={(event) => setValues((current) => ({ ...current, [row.id]: event.target.value }))} />
        </label>)}
        <label>Reason for correction<textarea required maxLength={500} value={reason} onChange={(event) => setReason(event.target.value)} /></label>
      </fieldset>
      {!review ? <button type="submit" disabled={busy}>Review correction</button> : null}{" "}
      <button type="button" className="secondary" disabled={busy} onClick={() => { setSelected(null); setReview(null); }}>Cancel correction</button>
    </form> : null}
    {!pending && review ? <section className="correction-review" aria-label="Correction preview">
      <h4>Review this correction</h4>
      <p>Saved time: {savedDuration(review.preview.before_microseconds)} → {savedDuration(review.preview.after_microseconds)}</p>
      <p>Coin adjustment: {signed(review.preview.coin_delta)} · Balance: {review.preview.balance_before} → {review.preview.balance_after}</p>
      {review.preview.coin_contribution_after === null ? <p>This session has no coin enrollment; no coins will be backfilled.</p> : null}
      <p>Tree: {review.preview.tree_before ?? "Not enrolled"} → {review.preview.tree_after ?? "Not enrolled"}</p>
      {review.preview.balance_after < 0 ? <p className="error">The corrected balance is negative. Owned species stay yours; new purchases are blocked.</p> : null}
      <ul aria-label="Corrected session dates">{review.preview.days.map((day) => <li key={day.date}>
        <strong>{day.date}</strong>: session {savedDuration(day.before_microseconds)} → {savedDuration(day.after_microseconds)}
        <p>Day total: {savedDuration(day.day_total_before_microseconds)} → {savedDuration(day.day_total_after_microseconds)} ·
          Streak goal: {day.qualified_before ? "Qualified" : "Below goal"} → {day.qualified_after ? "Qualified" : "Below goal"}</p>
      </li>)}</ul>
      <p className="muted">Dates use {review.preview.timezone}. Reports and streaks use these corrected intervals. Task completion and closed-week history stay as saved. Reverse through another reviewed correction; the audit and initial award remain.</p>
      <button type="button" disabled={busy} onClick={applyReviewed}>Apply correction</button>{" "}
      <button type="button" className="secondary" disabled={busy} onClick={() => setReview(null)}>Back to editing</button>
    </section> : null}
    {sessions?.length === 0 ? <p>No saved sessions yet.</p> : null}
    <ul className="stats-task-list" aria-label="Saved sessions">{sessions?.map((session) => <li key={session.id}>
      <span className="muted">{session.project_name}{session.parent_title ? ` / ${session.parent_title}` : ""}</span>
      <strong>{session.task_title}</strong><time dateTime={session.finished_at}>{new Date(session.finished_at).toLocaleString()}</time>
      <span>{savedDuration(session.active_microseconds)} · Original outcome: {session.outcome.replaceAll("_", " ")}</span>
      <span>{session.coin_contribution === null ? "Not enrolled for coins" : `${session.coin_contribution} coins after adjustments`}</span>
      {session.blocked_reason ? <p className="muted">{session.blocked_reason}</p> : null}
      <button type="button" disabled={busy || Boolean(pending) || Boolean(selected) || Boolean(session.blocked_reason)} onClick={() => edit(session)}>Correct saved time</button>
      {session.history.length ? <details><summary>Correction history ({session.history.length})</summary>
        <ul>{session.history.map((entry) => <li key={entry.operation_id}><p>{entry.reason}</p>
          <time dateTime={entry.created_at}>{new Date(entry.created_at).toLocaleString()}</time>
          <p>{savedDuration(entry.before.reduce((total, row) => total + row.active_microseconds, 0))} → {savedDuration(entry.after.reduce((total, row) => total + row.active_microseconds, 0))}</p>
        </li>)}</ul>
        <button type="button" disabled={busy || Boolean(pending) || Boolean(selected) || Boolean(session.blocked_reason)} onClick={() => edit(session, true)}>Prepare reversal of latest correction</button>
      </details> : null}
    </li>)}</ul>
  </section>;
}
