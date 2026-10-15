import { useCallback, useEffect, useId, useRef, useState } from "react";
import { ApiError, assignTask, getPlanning, movePlacement, removePlacement, setTaskCompletion, type Placement, type Planning, type Project, type Task } from "./api";

const fullDate = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeZone: "UTC" });
const dayName = new Intl.DateTimeFormat(undefined, { weekday: "long", timeZone: "UTC" });
const shortDate = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", timeZone: "UTC" });
const plainDate = (date: string) => new Date(`${date}T00:00:00Z`);
export const showDate = (date: string) => fullDate.format(plainDate(date));

/** Date-only arithmetic is deliberately independent of the browser timezone/DST. */
export function addDays(date: string, amount: number): string {
  const next = plainDate(date);
  next.setUTCDate(next.getUTCDate() + amount);
  return next.toISOString().slice(0, 10);
}

function message(error: unknown): string {
  return error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
}

export function usePlanning() {
  const [plan, setPlan] = useState<Planning | null>(null);
  const [selectedDay, setSelectedDay] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const request = useRef<AbortController | null>(null);
  // Retain the requested destination while it loads or fails. A mutation refresh
  // must not cancel a pending navigation and silently return to the old week.
  const destination = useRef<{ week: string | undefined; chooseToday: boolean }>({ week: undefined, chooseToday: true });

  const load = useCallback(async (target: string | undefined, chooseToday = false) => {
    request.current?.abort();
    destination.current = { week: target, chooseToday };
    const controller = new AbortController();
    request.current = controller;
    setLoading(true);
    setError(null);
    try {
      const loaded = await getPlanning(target, controller.signal);
      if (controller.signal.aborted) return true;
      destination.current = { week: loaded.week_start, chooseToday: false };
      setPlan(loaded);
      setSelectedDay((current) => {
        if (chooseToday || !current) return loaded.today;
        return current >= loaded.week_start && current <= loaded.week_end ? current : loaded.week_start;
      });
      return true;
    } catch (caught) {
      if (!controller.signal.aborted) setError(message(caught));
      return controller.signal.aborted;
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(undefined, true);
    return () => request.current?.abort();
  }, [load]);

  const refresh = useCallback(() => load(destination.current.week, destination.current.chooseToday), [load]);
  const navigate = useCallback((date: string | undefined) => load(date, date === undefined), [load]);
  return { plan, selectedDay, setSelectedDay, loading, error, refresh, navigate };
}

type Run = (work: () => Promise<unknown>, done: string) => Promise<void>;

/** Kept with the task list, so unscheduled work and dates in other weeks remain accessible. */
export function TaskPlanning({ task, plan, selectedDay, onRun }: { task: Task; plan: Planning | null; selectedDay: string; onRun: Run }) {
  if (task.subtask_count > 0) return <p className="planning-hint muted">Plan the subtasks below.</p>;
  if (!plan) return null;
  const placements = plan.placements.filter((placement) => placement.task_id === task.id)
    .sort((a, b) => a.planned_date.localeCompare(b.planned_date));
  return (
    <div className="task-planning">
      <p className="planning-summary muted">
        {placements.length ? `Planned: ${placements.map((placement) => showDate(placement.planned_date)).join(" · ")}` : "Unscheduled"}
      </p>
      <details>
        <summary>{placements.length ? "Move or remove plan" : "Plan task"}</summary>
        <p className="planning-hint muted">One planned day per task or subtask. Split multi-day work into subtasks. Deadlines stay unchanged.</p>
        {!placements.length ? <AssignForm key={selectedDay} task={task} initialDate={selectedDay || plan.today} onRun={onRun} /> : null}
        {placements.length ? (
          <ul className="placement-list">
            {placements.map((placement) => (
              <li key={placement.id}>
                <p>Planned {showDate(placement.planned_date)}</p>
                <PlacementActions key={`${placement.id}-${placement.planned_date}`} task={task} placement={placement} onRun={onRun} />
              </li>
            ))}
          </ul>
        ) : null}
      </details>
    </div>
  );
}

function AssignForm({ task, initialDate, onRun }: { task: Task; initialDate: string; onRun: Run }) {
  const [date, setDate] = useState(initialDate);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const id = useId();
  return (
    <form className="planning-form" onSubmit={async (event) => {
      event.preventDefault();
      if (!date || busy) return;
      setBusy(true);
      setError(null);
      try { await onRun(() => assignTask(task.id, date), `Planned “${task.title}” for ${showDate(date)}.`); }
      catch (caught) { setError(message(caught)); }
      finally { setBusy(false); }
    }}>
      <div className="field-row">
        <div className="field">
          <label htmlFor={id}>Planned date for “{task.title}”</label>
          <input id={id} type="date" value={date} required onChange={(event) => setDate(event.target.value)} disabled={busy} />
        </div>
        <button type="submit" disabled={busy || !date}>{busy ? "Saving…" : "Add to day"}</button>
      </div>
      {error ? <p role="alert" className="error">{error}</p> : null}
    </form>
  );
}

function PlacementActions({ task, placement, onRun }: { task: Task; placement: Placement; onRun: Run }) {
  const [date, setDate] = useState(placement.planned_date);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const id = useId();
  async function save(work: () => Promise<unknown>, done: string) {
    if (busy) return;
    setBusy(true);
    setError(null);
    try { await onRun(work, done); }
    catch (caught) { setError(message(caught)); }
    finally { setBusy(false); }
  }
  return (
    <form className="planning-form" onSubmit={(event) => {
      event.preventDefault();
      if (date && date !== placement.planned_date) void save(() => movePlacement(placement.id, date), `Moved “${task.title}” to ${showDate(date)}.`);
    }}>
      <div className="field">
        <label htmlFor={id}>Move “{task.title}” from {showDate(placement.planned_date)} to</label>
        <input id={id} type="date" value={date} required disabled={busy} onChange={(event) => setDate(event.target.value)} />
      </div>
      <div className="form-actions">
        <button type="submit" disabled={busy || !date || date === placement.planned_date}>{busy ? "Saving…" : "Move placement"}</button>
        <button type="button" className="link" disabled={busy} onClick={() => void save(() => removePlacement(placement.id), `Removed “${task.title}” from ${showDate(placement.planned_date)}. Task kept.`)}>Remove from plan</button>
      </div>
      {error ? <p role="alert" className="error">{error}</p> : null}
    </form>
  );
}

function PlannedCard({ task, placement, context, onRun, locked }: { task: Task; placement: Placement; context: string; onRun: Run; locked: boolean }) {
  const id = useId();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  return (
    <li className={`planned-card${task.completed ? " planned-card-done" : ""}`}>
      <p className="planned-context muted">{context}</p>
      <div className="planned-title">
        <input id={id} type="checkbox" checked={task.completed} disabled={busy || locked} aria-label={`${task.title}, planned ${showDate(placement.planned_date)}`} onChange={async (event) => {
          const complete = event.target.checked;
          setBusy(true);
          setError(null);
          try { await onRun(() => setTaskCompletion(task.id, complete), complete ? "Task marked complete." : "Task reopened."); }
          catch (caught) { setError(message(caught)); }
          finally { setBusy(false); }
        }} />
        <label htmlFor={id}>{task.title}</label>
      </div>
      <p className="planned-meta muted">Planned {showDate(placement.planned_date)}</p>
      {task.deadline ? <p className="planned-meta muted">Due {showDate(task.deadline)}</p> : null}
      {task.estimate_minutes ? <p className="planned-meta muted">{task.estimate_minutes} min estimated</p> : null}
      {error ? <p role="alert" className="error">{error}</p> : null}
      <details>
        <summary>Move or remove</summary>
        <PlacementActions key={`${placement.id}-${placement.planned_date}`} task={task} placement={placement} onRun={onRun} />
      </details>
    </li>
  );
}

export function WeeklyPlanner({ state, projects, onRun, locked }: { state: ReturnType<typeof usePlanning>; projects: Project[]; onRun: Run; locked: boolean }) {
  const { plan, selectedDay, setSelectedDay, loading, error, navigate, refresh } = state;
  const days = plan ? Array.from({ length: 7 }, (_, index) => addDays(plan.week_start, index)) : [];
  const tasksById = new Map(plan?.tasks.map((task) => [task.id, task]) ?? []);
  const projectById = new Map(projects.map((project) => [project.id, project.name]));
  return (
    <section className="weekly-planner" aria-labelledby="planning-heading" aria-busy={loading}>
      <div className="planner-heading">
        <div>
          <h2 id="planning-heading">Weekly plan</h2>
          <p className="muted">{plan ? `${showDate(plan.week_start)} – ${showDate(plan.week_end)}` : "Loading week…"}</p>
        </div>
        <nav className="week-navigation" aria-label="Week navigation">
          <button type="button" className="secondary" aria-label="Previous week" disabled={!plan || loading} onClick={() => void navigate(addDays(plan!.week_start, -7))}>← Previous</button>
          <button type="button" className="secondary" disabled={loading} onClick={() => void navigate(undefined)}>Today</button>
          <button type="button" className="secondary" aria-label="Next week" disabled={!plan || loading} onClick={() => void navigate(addDays(plan!.week_start, 7))}>Next →</button>
        </nav>
      </div>
      {plan ? <p className="timezone-note muted">Today is {showDate(plan.today)} · {plan.timezone}</p> : null}
      <p className="planning-hint muted">Plan a task from the project list. One planned day per task or subtask. Split multi-day work into subtasks.</p>
      {error ? <p role="alert" className="error">{error} <button type="button" className="link" onClick={() => void refresh()}>Retry weekly plan</button></p> : null}
      {plan ? (
        <>
          <div className="day-selector" role="group" aria-label="Selected day">
            {days.map((date) => (
              <button key={date} type="button" className={selectedDay === date ? "day-choice day-choice-on" : "day-choice"} aria-pressed={selectedDay === date} onClick={() => setSelectedDay(date)}>
                <span>{dayName.format(plainDate(date)).slice(0, 3)}</span><span>{shortDate.format(plainDate(date))}</span>{date === plan.today ? <span className="today-mark">Today</span> : null}
              </button>
            ))}
          </div>
          <div className="week-board">
            {days.map((date) => {
              const placements = plan.placements.filter((placement) => placement.planned_date === date);
              return (
                <section key={date} className={`day-column${selectedDay === date ? " day-selected" : ""}${date === plan.today ? " day-today" : ""}`} aria-label={`${dayName.format(plainDate(date))}, ${showDate(date)}`}>
                  <h3>{dayName.format(plainDate(date))}<span>{shortDate.format(plainDate(date))}{date === plan.today ? " · Today" : ""}</span></h3>
                  {placements.length ? (
                    <ul className="day-placements">
                      {placements.map((placement) => {
                        const task = tasksById.get(placement.task_id);
                        if (!task) return null;
                        const parent = task.parent_id ? tasksById.get(task.parent_id) : null;
                        const context = [projectById.get(task.project_id) ?? "Project", parent?.title].filter(Boolean).join(" / ");
                        return <PlannedCard key={placement.id} task={task} placement={placement} context={context} onRun={onRun} locked={locked} />;
                      })}
                    </ul>
                  ) : <p className="empty-day muted">Nothing planned</p>}
                </section>
              );
            })}
          </div>
        </>
      ) : null}
    </section>
  );
}
