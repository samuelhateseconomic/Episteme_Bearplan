import { useCallback, useEffect, useId, useRef, useState, type FormEvent } from "react";
import { ApiError, controlTimer, getTimer, startTimer, type Planning, type Project, type Task, type TimerSession, type TimerState } from "./api";

const message = (error: unknown) => error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
const PENDING_KEY = "bearplans.timer.pending";
interface PendingRequest { fingerprint: string; operationId: string }

function readPending(): PendingRequest | null {
  try {
    const value: unknown = JSON.parse(sessionStorage.getItem(PENDING_KEY) ?? "null");
    if (value && typeof value === "object" && "fingerprint" in value && "operationId" in value
      && typeof value.fingerprint === "string" && typeof value.operationId === "string") return value as PendingRequest;
  } catch { /* An unavailable browser store does not prevent tracking. */ }
  return null;
}

/** The service owns state and saves time. This hook only interpolates its display. */
export function useCountdown() {
  const [state, setState] = useState<TimerState | null>(null);
  const [sampledAt, setSampledAt] = useState(0);
  const [displayAt, setDisplayAt] = useState(0);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(false);
  const pending = useRef<PendingRequest | null>(readPending());
  const request = useRef<AbortController | null>(null);
  const generation = useRef(0);

  const clearPending = useCallback(() => {
    pending.current = null;
    try { sessionStorage.removeItem(PENDING_KEY); } catch { /* See readPending. */ }
  }, []);

  const accept = useCallback((loaded: TimerState) => {
    const now = performance.now();
    setState(loaded);
    setSampledAt(now);
    setDisplayAt(now);
    setLoadError(null);
    // A lost Start response can be acknowledged by a later authoritative read.
    if (pending.current && [loaded.active_session, loaded.last_session].some((session) => session?.start_operation_id === pending.current?.operationId)) clearPending();
  }, [clearPending]);

  const refresh = useCallback(async () => {
    if (busyRef.current) return;
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    const current = ++generation.current;
    try {
      const loaded = await getTimer(controller.signal);
      if (!controller.signal.aborted && current === generation.current) accept(loaded);
    } catch (caught) {
      if (!controller.signal.aborted && current === generation.current) setLoadError(message(caught));
    }
  }, [accept]);

  useEffect(() => {
    void refresh();
    const poll = window.setInterval(() => void refresh(), 2000);
    const tick = window.setInterval(() => setDisplayAt(performance.now()), 250);
    const recheck = () => void refresh();
    window.addEventListener("focus", recheck);
    document.addEventListener("visibilitychange", recheck);
    return () => {
      window.clearInterval(poll);
      window.clearInterval(tick);
      window.removeEventListener("focus", recheck);
      document.removeEventListener("visibilitychange", recheck);
      request.current?.abort();
      generation.current += 1;
    };
  }, [refresh]);

  const active = state?.active_session ?? null;
  const remaining = active ? Math.max(0, active.remaining_seconds - (active.state === "running" ? Math.max(0, displayAt - sampledAt) / 1000 : 0)) : 0;
  // Reaching zero in a page never finalizes a session. Ask the service to resolve it.
  const expiredId = active?.state === "running" && remaining <= 0 ? active.id : null;
  useEffect(() => { if (expiredId) void refresh(); }, [expiredId, refresh]);

  async function mutate(fingerprint: string, work: (operationId: string) => Promise<TimerState>) {
    if (busyRef.current) return false;
    let saved = false;
    busyRef.current = true;
    setBusy(true);
    setActionError(null);
    request.current?.abort();
    generation.current += 1;
    if (pending.current?.fingerprint !== fingerprint) {
      pending.current = { fingerprint, operationId: crypto.randomUUID() };
      try { sessionStorage.setItem(PENDING_KEY, JSON.stringify(pending.current)); } catch { /* Retry remains safe within this page. */ }
    }
    try {
      accept(await work(pending.current.operationId));
      clearPending();
      saved = true;
    } catch (caught) {
      setActionError(`${message(caught)} Your inputs are kept. Refresh timer to check the saved state, or retry.`);
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
    await refresh();
    return saved;
  }

  function start(taskId: string, minutes: number) {
    return mutate(JSON.stringify(["start", taskId, minutes]), (id) => startTimer(id, taskId, minutes));
  }

  function control(action: "pause" | "resume" | "finish", discardUncertain = false) {
    if (!active) return Promise.resolve();
    return mutate(JSON.stringify([action, active.id, active.revision, discardUncertain]), (id) => controlTimer(active.id, action, {
      operation_id: id, expected_revision: active.revision, ...(discardUncertain ? { discard_uncertain: true } : {}),
    }));
  }

  function retry() { setActionError(null); void refresh(); }
  return { state, active, remaining, busy, error: actionError ?? loadError, start, control, refresh: retry };
}

export type Countdown = ReturnType<typeof useCountdown>;

/** Shared by current-task entry points; historical cards never offer this action. */
export function StartTrackingButton({ task, onTrack, disabled = false }: { task: Task; onTrack: () => void; disabled?: boolean }) {
  const hintId = useId();
  if (task.subtask_count > 0) return null;
  return <div className="tracking-entry">
    <button type="button" className="link" disabled={disabled || task.completed} aria-describedby={task.completed ? hintId : undefined} onClick={onTrack}>Start tracking</button>
    {task.completed ? <p id={hintId} className="tracking-hint muted">Reopen this task to start a new session. An existing session continues.</p> : null}
  </div>;
}

export function formatRemaining(seconds: number): string {
  const total = Math.max(0, Math.ceil(seconds));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor(total % 3600 / 60);
  const rest = String(total % 60).padStart(2, "0");
  return hours ? `${hours}:${String(minutes).padStart(2, "0")}:${rest}` : `${String(minutes).padStart(2, "0")}:${rest}`;
}

function sessionContext(session: TimerSession) {
  return [session.project_name, session.parent_title].filter(Boolean).join(" / ");
}

function TimerControls({ timer, compact = false }: { timer: Countdown; compact?: boolean }) {
  const active = timer.active;
  if (!active) return null;
  if (active.state === "needs_review") return compact ? null : <>
    <p className="error">Needs review: {active.review_reason ?? "This session was interrupted. Its uncertain time has not been credited."}</p>
    <p className="muted">Save only the confirmed time shown and exclude the uncertain gap. Detailed recovery and correction are part of the next build.</p>
    <button type="button" disabled={timer.busy} onClick={() => void timer.control("finish", true)}>Save confirmed time and finish</button>
  </>;
  return <div className="form-actions">
    <button type="button" disabled={timer.busy || active.state === "running" && timer.remaining <= 0} onClick={() => void timer.control(active.state === "running" ? "pause" : "resume")}>
      {active.state === "running" ? "Pause" : "Resume"}
    </button>
    <button type="button" className="secondary" disabled={timer.busy} onClick={() => void timer.control("finish")}>Finish early</button>
  </div>;
}

export function CompactTimer({ timer, onOpen }: { timer: Countdown; onOpen: () => void }) {
  if (!timer.active) return null;
  return <aside className="compact-timer" aria-label="Active countdown">
    <div className="compact-summary">
      <strong>{timer.active.task_title}</strong>
      <span>{timer.active.state === "needs_review" ? "Needs review" : `${formatRemaining(timer.remaining)} · ${timer.active.state === "paused" ? "Paused" : "Running"}`}</span>
    </div>
    <TimerControls timer={timer} compact />
    <button type="button" className="link" onClick={onOpen}>Open Track</button>
  </aside>;
}

export function TrackScreen({ timer, plan, projects, requestedTaskId, requestToken = 0, visible, planError, onRefreshTasks }: {
  timer: Countdown; plan: Planning | null; projects: Project[]; requestedTaskId: string | null; requestToken?: number; visible: boolean;
  planError?: string | null; onRefreshTasks?: () => void;
}) {
  const [taskId, setTaskId] = useState("");
  const [minutes, setMinutes] = useState("25");
  const heading = useRef<HTMLHeadingElement>(null);
  const eligibleTasks = plan?.tasks.filter((task) => task.subtask_count === 0 && !task.completed) ?? [];
  useEffect(() => { if (requestedTaskId) setTaskId(requestedTaskId); }, [requestedTaskId, requestToken]);
  useEffect(() => { if (visible) heading.current?.focus(); }, [visible]);
  const selectedTask = eligibleTasks.find((task) => task.id === taskId);
  const validDuration = /^\d+$/.test(minutes) && Number(minutes) >= 1 && Number(minutes) <= 180;
  const active = timer.active;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTask || !validDuration || timer.busy || active) return;
    // Another tab may have completed this task since the choices were loaded.
    // Refresh after a rejected Start while retaining the chosen duration.
    if (!await timer.start(selectedTask.id, Number(minutes))) onRefreshTasks?.();
  }

  return <section className="track-screen" aria-labelledby="track-heading" hidden={!visible}>
    <h2 id="track-heading" ref={heading} tabIndex={-1}>Track</h2>
    <p className="muted">Choose an incomplete task and make time for it. Unscheduled tasks are welcome.</p>
    {timer.state === null ? <p className="muted">Loading timer…</p> : null}
    {active ? <section className="countdown-card" aria-label="Current session" aria-busy={timer.busy}>
      <p className="muted">{sessionContext(active)}</p>
      <h3>{active.task_title}</h3>
      <p className="countdown-time" role="timer" aria-label="Time remaining">{formatRemaining(timer.remaining)}</p>
      <p>{active.state === "needs_review" ? "Needs review" : active.state === "paused" ? "Paused · paused time is excluded" : timer.remaining <= 0 ? "Waiting for the service to save the outcome…" : "Running"} · {active.duration_minutes} minute countdown</p>
      {active.state === "needs_review" ? <p>Confirmed active time: {formatRemaining(Math.floor(active.active_seconds))}</p> : null}
      <TimerControls timer={timer} />
      {active.state !== "needs_review" ? <p className="muted">Tracking continues when you switch screens, hide this tab, or close the browser while the service remains running.</p> : null}
    </section> : <form className="countdown-form" onSubmit={submit} aria-busy={timer.busy}>
      <div className="field">
        <label htmlFor="tracking-task">Task to track</label>
        <select id="tracking-task" value={taskId} disabled={timer.busy || !plan || eligibleTasks.length === 0} onChange={(event) => setTaskId(event.target.value)} required>
          <option value="">Choose a task or subtask</option>
          {eligibleTasks.map((task) => {
            const project = projects.find((item) => item.id === task.project_id);
            const parent = plan?.tasks.find((item) => item.id === task.parent_id);
            return <option key={task.id} value={task.id}>{[project?.name, parent?.title, task.title].filter(Boolean).join(" / ")}</option>;
          })}
        </select>
        {onRefreshTasks ? <button type="button" className="link refresh-task-choices" disabled={timer.busy} onClick={onRefreshTasks}>Refresh task choices</button> : null}
        {planError ? <p role="alert" className="error">{planError} Refresh task choices to try again.</p> : null}
      </div>
      <div className="field">
        <label htmlFor="tracking-duration">Duration (minutes)</label>
        <input id="tracking-duration" type="number" inputMode="numeric" min="1" max="180" step="1" required value={minutes} disabled={timer.busy} onChange={(event) => setMinutes(event.target.value)} aria-describedby="duration-hint" />
        <p id="duration-hint" className="muted">Whole minutes from 1 to 180.</p>
      </div>
      {!plan ? <p className="muted">Load the plan to select a task.</p> : eligibleTasks.length === 0 ? <p className="muted">No incomplete tasks to track. Add a task or reopen a completed task in Plan. For a task with subtasks, track an incomplete subtask.</p> : taskId && !selectedTask ? <p className="error">This task is no longer available for a new session. Choose an incomplete task or reopen it in Plan.</p> : null}
      <button type="submit" disabled={!selectedTask || !validDuration || timer.busy || timer.state === null}>{timer.busy ? "Starting…" : "Start countdown"}</button>
    </form>}
    <p className="tracking-rule">Finishing a countdown saves the session. Complete the task separately in Plan.</p>
    {timer.state?.last_session ? <SavedSession session={timer.state.last_session} /> : null}
    <p className="recovery-note">Recovery is provisional in this build. Service interruptions or uncertain clock or sleep gaps need review and do not silently earn time. Full sleep, crash, and clock-change recovery has not passed its acceptance checks.</p>
  </section>;
}

function SavedSession({ session }: { session: TimerSession }) {
  const outcome = session.outcome === "completed" ? "Countdown completed" : session.outcome === "interrupted" ? "Interrupted · uncertain time excluded" : "Finished early";
  return <section className="saved-session" aria-label="Saved session outcome">
    <h3>Session saved</h3>
    <p><strong>{session.task_title}</strong> · {sessionContext(session)}</p>
    <p>{outcome} · {formatRemaining(Math.floor(session.active_seconds))} active time of {session.duration_minutes} {session.duration_minutes === 1 ? "minute" : "minutes"}.</p>
    <p className="muted">Started {new Date(session.started_at).toLocaleString()}{session.finished_at ? ` · Finished ${new Date(session.finished_at).toLocaleString()}` : ""}. Session history stays attached to when this work occurred.</p>
  </section>;
}
