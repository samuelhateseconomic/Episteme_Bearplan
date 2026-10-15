import { useState } from "react";
import {
  ApiError, applyCarryover, closeWeek, getCarryover, previewCarryover, previewCloseWeek,
  type CarryoverOptions, type CarryoverPreview, type CarryoverSelection, type ClosePreview,
  type HistoricalTask, type Planning, type Task,
} from "./api";

type Run = (work: () => Promise<unknown>, done: string) => Promise<void>;
const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeZone: "UTC" });
const showDate = (date: string) => dateFormat.format(new Date(`${date}T00:00:00Z`));
const message = (error: unknown) => error instanceof ApiError ? error.message : "Something went wrong. Please try again.";

export function WeekTaskDetails({ task, context }: { task: Task; context: string }) {
  return <>
    <p className="planned-context muted">{context}</p>
    <strong className="week-task-title">{task.title}</strong>
    {task.deadline ? <p className="planned-meta muted">Due {showDate(task.deadline)}</p> : null}
    {task.estimate_minutes ? <p className="planned-meta muted">{task.estimate_minutes} min estimated</p> : null}
    {task.notes ? <p className="task-notes">{task.notes}</p> : null}
  </>;
}

export const historicalContext = (task: HistoricalTask) => [task.project_name, task.parent_title].filter(Boolean).join(" / ");

export function WeekActions({ plan, onRun, locked }: { plan: Planning; onRun: Run; locked: boolean }) {
  return plan.closed_week
    ? <Carryover week={plan.week_start} onRun={onRun} locked={locked} />
    : <EndWeek week={plan.week_start} onRun={onRun} locked={locked} />;
}

function EndWeek({ week, onRun, locked }: { week: string; onRun: Run; locked: boolean }) {
  const [preview, setPreview] = useState<ClosePreview | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function review() {
    if (busy || locked) return;
    setBusy(true);
    setError(null);
    try { setPreview(await previewCloseWeek(week)); }
    catch (caught) { setError(message(caught)); }
    finally { setBusy(false); }
  }
  async function close() {
    if (!preview || busy || locked) return;
    setBusy(true);
    setError(null);
    try { await onRun(() => closeWeek(week, preview.preview_token), "Week closed. Its plan and completion are preserved in history."); }
    catch (caught) { setError(message(caught)); }
    finally { setBusy(false); }
  }
  const tasks = new Map(preview?.snapshot.tasks.map((task) => [task.id, task]));
  return <div className="week-actions">
    <button type="button" className="secondary" disabled={busy || locked} onClick={() => void review()}>{busy ? "Working…" : preview ? "Refresh end-week preview" : "End Week"}</button>
    {preview ? <section className="week-review" aria-label="End week preview">
      <h3>Review before closing</h3>
      <p>{showDate(preview.snapshot.week_start)} – {showDate(preview.snapshot.week_end)}</p>
      <p>{preview.snapshot.completed} of {preview.snapshot.total} work items complete ({preview.snapshot.total ? Math.round(preview.snapshot.completed / preview.snapshot.total * 100) : 0}%).</p>
      <p className="muted">Closing saves this plan and its completion as history. Tasks stay unchanged. This build cannot reopen a closed week.</p>
      {preview.snapshot.placements.length ? <ul className="week-review-items">{preview.snapshot.placements.map((placement) => {
        const task = tasks.get(placement.task_id);
        return task ? <li key={placement.id}>
          <WeekTaskDetails task={task} context={historicalContext(task)} />
          <p className="planned-meta">Planned {showDate(placement.planned_date)} · {task.completed ? "Complete" : "Unfinished"}</p>
        </li> : null;
      })}</ul> : <p>No planned work. This week will close with 0 of 0 complete (0%).</p>}
      <div className="form-actions">
        <button type="button" disabled={busy || locked} onClick={() => void close()}>Close week</button>
        <button type="button" className="secondary" disabled={busy} onClick={() => { setPreview(null); setError(null); }}>Cancel</button>
      </div>
    </section> : null}
    {error ? <p role="alert" className="error">{error} Review the preview again if the week has changed.</p> : null}
  </div>;
}

function Carryover({ week, onRun, locked }: { week: string; onRun: Run; locked: boolean }) {
  const [options, setOptions] = useState<CarryoverOptions | null>(null);
  const [selected, setSelected] = useState<Record<string, string>>({});
  const [review, setReview] = useState<{ preview: CarryoverPreview; selections: CarryoverSelection[]; operationId: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  async function load() {
    if (busy || locked) return;
    setBusy(true);
    setError(null);
    try { setOptions(await getCarryover(week)); setSelected({}); setReview(null); }
    catch (caught) { setError(message(caught)); }
    finally { setBusy(false); }
  }
  function select(taskId: string, date: string | null) {
    setSelected((current) => {
      const next = { ...current };
      if (date === null) delete next[taskId];
      else next[taskId] = date;
      return next;
    });
    setReview(null);
    setError(null);
    setResult(null);
  }
  async function preview() {
    if (busy || locked || !Object.keys(selected).length) return;
    setBusy(true);
    setError(null);
    const selections = Object.entries(selected).map(([task_id, planned_date]) => ({ task_id, planned_date }));
    try { setReview({ preview: await previewCarryover(week, selections), selections, operationId: crypto.randomUUID() }); }
    catch (caught) { setError(message(caught)); }
    finally { setBusy(false); }
  }
  async function apply() {
    if (!review || busy || locked) return;
    setBusy(true);
    setError(null);
    try {
      await onRun(() => applyCarryover(week, review.operationId, review.preview.preview_token, review.selections), "Selected work carried over. The closed week is unchanged.");
      setResult(`Carried over ${review.selections.length} work item${review.selections.length === 1 ? "" : "s"}. The same tasks now have a plan in the following week.`);
      setReview(null);
      setSelected({});
      // The operation already succeeded. A read failure must not turn it into a
      // failed save or encourage the operator to apply a new operation blindly.
      try { setOptions(await getCarryover(week)); }
      catch { setOptions(null); }
    } catch (caught) { setError(message(caught)); }
    finally { setBusy(false); }
  }
  return <div className="week-actions">
    <button type="button" className="secondary" disabled={busy || locked} onClick={() => void load()}>{busy ? "Working…" : options ? "Refresh carryover choices" : "Carry unfinished work"}</button>
    {options ? <section className="week-review" aria-label="Carryover choices">
      <h3>Choose unfinished work to carry over</h3>
      <p>Destination: {showDate(options.destination_start)} – {showDate(options.destination_end)}.</p>
      <p className="muted">Choose dates and review before applying. Carryover keeps the same task, deadline and notes; the closed source week stays unchanged. Currently completed work is excluded.</p>
      {options.candidates.length ? <ul className="week-review-items">{options.candidates.map((candidate) => {
        const task = candidate.task ?? candidate.snapshot_task;
        const checked = candidate.task_id in selected;
        return <li key={candidate.task_id}>
          <label className="carryover-choice">
            <input type="checkbox" checked={checked} disabled={!candidate.eligible || busy || locked} onChange={(event) => select(candidate.task_id, event.target.checked ? options.destination_start : null)} />
            <span>{task.title}</span>
          </label>
          <p className="planned-context muted">{historicalContext(candidate.snapshot_task)}</p>
          {task.deadline ? <p className="planned-meta muted">Due {showDate(task.deadline)}</p> : null}
          {!candidate.eligible ? <p className="planned-meta muted">{candidate.reason ?? "This task is not available for carryover."}{candidate.existing_planned_date ? ` Existing plan: ${showDate(candidate.existing_planned_date)}.` : ""}</p> : null}
          {checked ? <div className="field"><label htmlFor={`carry-date-${candidate.task_id}`}>Carry “{task.title}” to</label><input id={`carry-date-${candidate.task_id}`} type="date" value={selected[candidate.task_id]} min={options.destination_start} max={options.destination_end} required disabled={busy || locked} onChange={(event) => select(candidate.task_id, event.target.value)} /></div> : null}
        </li>;
      })}</ul> : <p>No unfinished work was recorded at closure.</p>}
      <div className="form-actions">
        <button type="button" disabled={busy || locked || !Object.keys(selected).length || Object.values(selected).some((date) => date < options.destination_start || date > options.destination_end)} onClick={() => void preview()}>Review carryover</button>
        <button type="button" className="secondary" disabled={busy} onClick={() => { setOptions(null); setSelected({}); setReview(null); setError(null); }}>Cancel carryover</button>
      </div>
    </section> : null}
    {review ? <section className="week-review" aria-label="Carryover preview">
      <h3>Review destination plans</h3>
      <p>The following tasks will be planned in the week immediately after this closed week.</p>
      <ul className="week-review-items">{review.preview.items.map((item) => <li key={item.task_id}>
        <WeekTaskDetails task={item.task} context={[item.project_name, item.parent_title].filter(Boolean).join(" / ")} />
        <p>Planned {showDate(item.planned_date)}</p>
      </li>)}</ul>
      <button type="button" disabled={busy || locked} onClick={() => void apply()}>Apply carryover</button>
    </section> : null}
    {error ? <p role="alert" className="error">{error} Your selections are kept. Retry, or refresh choices and review again if task status has changed.</p> : null}
    {result ? <p role="status">{result}</p> : null}
  </div>;
}
