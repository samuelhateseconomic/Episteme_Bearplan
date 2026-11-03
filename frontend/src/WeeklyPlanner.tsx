import { useCallback, useEffect, useId, useRef, useState, type DragEvent } from "react";
import { ApiError, addGoogleEvent, assignTask, getPlanning, movePlacement, removePlacement, setPlacementTime, setTaskCompletion, type GoogleEvent, type Placement, type Planning, type Project, type Task } from "./api";
import { WeekActions, WeekTaskDetails, historicalContext } from "./WeekActions";
import { StartTrackingButton } from "./Countdown";

const fullDate = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeZone: "UTC" });
const dayName = new Intl.DateTimeFormat(undefined, { weekday: "long", timeZone: "UTC" });
const shortDate = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", timeZone: "UTC" });
const plainDate = (date: string) => new Date(`${date}T00:00:00Z`);
export const showDate = (date: string) => fullDate.format(plainDate(date));
const clock = new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit", timeZone: "UTC" });
export const showTime = (time: string) => clock.format(new Date(`1970-01-01T${time}:00Z`));
const showPlanned = (placement: Placement) => showDate(placement.planned_date) + (placement.start_time ? ` at ${showTime(placement.start_time)}` : "");

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
        {placements.length ? `Planned: ${placements.map(showPlanned).join(" · ")}` : "Unscheduled"}
      </p>
      <details>
        <summary>{placements.length ? "Move or remove plan" : "Plan task"}</summary>
        {!placements.length && !plan.closed_week ? <AssignForm key={selectedDay} task={task} initialDate={selectedDay || plan.today} onRun={onRun} /> : null}
        {!placements.length && plan.closed_week ? <p className="planning-hint muted">Viewing a closed week. Choose an open week to plan this task.</p> : null}
        {placements.length ? (
          <ul className="placement-list">
            {placements.map((placement) => (
              <li key={placement.id}>
                <p>Planned {showPlanned(placement)}</p>
                <PlacementActions key={`${placement.id}-${placement.planned_date}-${placement.start_time ?? ""}`} task={task} placement={placement} onRun={onRun} />
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
  return (<>
    <TimeForm task={task} placement={placement} onRun={onRun} />
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
  </>);
}

function TimeForm({ task, placement, onRun }: { task: Task; placement: Placement; onRun: Run }) {
  const saved = placement.start_time ?? "";
  const [time, setTime] = useState(saved);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const id = useId();
  async function save(value: string | null) {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await onRun(() => setPlacementTime(placement.id, value), value
        ? `“${task.title}” starts at ${showTime(value)} on ${showDate(placement.planned_date)}. Google Calendar will remind you 30 minutes before.`
        : `Removed the start time from “${task.title}”.`);
    } catch (caught) { setError(message(caught)); }
    finally { setBusy(false); }
  }
  return (
    <form className="planning-form time-form" onSubmit={(event) => { event.preventDefault(); if (time && time !== saved) void save(time); }}>
      <div className="field">
        <label htmlFor={id}>Start time on {showDate(placement.planned_date)} (optional)</label>
        <input id={id} type="time" value={time} disabled={busy} onChange={(event) => setTime(event.target.value)} />
      </div>
      <div className="form-actions">
        <button type="submit" disabled={busy || !time || time === saved}>{busy ? "Saving…" : "Save time"}</button>
        {saved ? <button type="button" className="link" disabled={busy} onClick={() => { setTime(""); void save(null); }}>Clear time</button> : null}
      </div>
      {error ? <p role="alert" className="error">{error}</p> : null}
    </form>
  );
}

const eventClock = new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" });

export function CalendarEvents({ events, date, onRun, locked }: { events: GoogleEvent[]; date: string; onRun: Run; locked: boolean }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  if (!events.length) return null;
  // Closed by default: a busy week has about 28 events (user decision, 2026-11-03).
  return <details className="day-events">
    <summary>From your calendar ({events.length})</summary>
    <ul aria-label={`Calendar events, ${showDate(date)}`}>
      {events.map((event) => {
        const when = event.all_day ? "All day" : `${eventClock.format(new Date(event.start_at ?? ""))} – ${eventClock.format(new Date(event.end_at ?? event.start_at ?? ""))}`;
        const key = `${event.calendar_id}/${event.event_id}`;
        return <li key={key} className="day-event" style={event.color ? { borderLeftColor: event.color } : undefined}>
          <p className="day-event-title">{event.summary}</p>
          <p className="planned-meta muted">{when} · {event.calendar_summary}{event.location ? ` · ${event.location}` : ""}</p>
          {event.task_id ? <p className="planned-meta">Added as a task</p>
            : <button type="button" className="link" disabled={locked || busy !== null} onClick={async () => {
              setBusy(key);
              setError(null);
              try { await onRun(() => addGoogleEvent(event.calendar_id, event.event_id), `Added “${event.summary}” as a task${event.first_day >= date ? ` planned ${showDate(event.first_day)}` : ""}.`); }
              catch (caught) { setError(message(caught)); }
              finally { setBusy(null); }
            }}>{busy === key ? "Adding…" : "Add as task"}</button>}
        </li>;
      })}
    </ul>
    {error ? <p role="alert" className="error">{error}</p> : null}
  </details>;
}

type DraggedPlacement = { placement: Placement; title: string };
type DragControls = { start: (event: DragEvent<HTMLElement>, placement: Placement, task: Task) => void; end: () => void };

function PlannedCard({ task, placement, context, onRun, locked, onTrack, drag }: { task: Task; placement: Placement; context: string; onRun: Run; locked: boolean; onTrack?: (taskId: string) => void; drag: DragControls }) {
  const id = useId();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  return (
    <li className={`planned-card${task.completed ? " planned-card-done" : ""}`} onDragStart={(event) => {
      if (!(event.target instanceof Element) || !event.target.closest(".placement-drag-handle")) event.preventDefault();
    }}>
      <div className="planned-card-heading">
        <span className="placement-drag-handle" draggable={!busy && !locked} role="img" aria-label={`Move “${task.title}” from ${showDate(placement.planned_date)}`} title="Move planned task. Date controls are available below." onDragStart={(event) => drag.start(event, placement, task)} onDragEnd={drag.end}>
          <svg width="12" height="18" viewBox="0 0 12 18" fill="currentColor" aria-hidden="true"><circle cx="3" cy="3" r="1.5" /><circle cx="9" cy="3" r="1.5" /><circle cx="3" cy="9" r="1.5" /><circle cx="9" cy="9" r="1.5" /><circle cx="3" cy="15" r="1.5" /><circle cx="9" cy="15" r="1.5" /></svg>
        </span>
        <p className="planned-context muted">{context}</p>
      </div>
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
      {placement.start_time ? <p className="planned-meta">At {showTime(placement.start_time)}</p> : null}
      {task.deadline ? <p className="planned-meta muted">Due {showDate(task.deadline)}</p> : null}
      {task.estimate_minutes ? <p className="planned-meta muted">{task.estimate_minutes} min estimated</p> : null}
      {onTrack ? <StartTrackingButton task={task} onTrack={() => onTrack(task.id)} disabled={busy || locked} /> : null}
      {error ? <p role="alert" className="error">{error}</p> : null}
      <details>
        <summary>Move or remove</summary>
        <PlacementActions key={`${placement.id}-${placement.planned_date}-${placement.start_time ?? ""}`} task={task} placement={placement} onRun={onRun} />
      </details>
    </li>
  );
}

export function WeeklyPlanner({ state, projects, onRun, locked, onTrack }: { state: ReturnType<typeof usePlanning>; projects: Project[]; onRun: Run; locked: boolean; onTrack?: (taskId: string) => void }) {
  const { plan, selectedDay, setSelectedDay, loading, error, navigate, refresh } = state;
  const [dragged, setDragged] = useState<DraggedPlacement | null>(null);
  const draggedRef = useRef<DraggedPlacement | null>(null);
  const [overDay, setOverDay] = useState<string | null>(null);
  const [dragBusy, setDragBusy] = useState(false);
  const dragBusyRef = useRef(false);
  const [dragError, setDragError] = useState<string | null>(null);
  const endDrag = useCallback(() => {
    draggedRef.current = null;
    setDragged(null);
    setOverDay(null);
  }, []);
  useEffect(() => {
    const key = (event: KeyboardEvent) => { if (event.key === "Escape") endDrag(); };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [endDrag]);
  useEffect(endDrag, [plan?.week_start, Boolean(plan?.closed_week), endDrag]);
  const days = plan ? Array.from({ length: 7 }, (_, index) => addDays(plan.week_start, index)) : [];
  // Events from the user's followed Google calendars (read-only), sent with the week.
  const events = plan?.calendar_events ?? [];
  const tasksById = new Map(plan?.tasks.map((task) => [task.id, task]) ?? []);
  const projectById = new Map(projects.map((project) => [project.id, project.name]));
  const closed = plan?.closed_week;
  const historicalTasks = new Map(closed?.tasks.map((task) => [task.id, task]) ?? []);
  const visiblePlacements = closed?.placements ?? plan?.placements ?? [];
  const uniqueTasks = new Set(visiblePlacements.filter((placement) => plan && placement.planned_date >= plan.week_start && placement.planned_date <= plan.week_end).map((placement) => placement.task_id));
  const leafTasks = [...uniqueTasks].map((id) => tasksById.get(id)).filter((task): task is Task => !!task && !task.subtask_count);
  const completed = closed?.completed ?? leafTasks.filter((task) => task.completed).length;
  const total = closed?.total ?? leafTasks.length;
  const dragLocked = locked || loading || dragBusy || !!closed;
  const duplicateDay = (date: string, item = draggedRef.current) => !!item && !!plan?.placements.some((placement) => placement.task_id === item.placement.task_id && placement.planned_date === date && placement.id !== item.placement.id);
  const destinationClass = (date: string) => !dragged || dragLocked ? "" : date === dragged.placement.planned_date ? " drop-source" : duplicateDay(date) ? ` drop-conflict${overDay === date ? " drop-over" : ""}` : ` drop-valid${overDay === date ? " drop-over" : ""}`;
  function dragOver(event: DragEvent<HTMLElement>, date: string) {
    if (!draggedRef.current || dragLocked) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    setOverDay(date);
  }
  async function drop(event: DragEvent<HTMLElement>, date: string) {
    const item = draggedRef.current;
    if (!item) return;
    event.preventDefault();
    endDrag();
    if (dragLocked || dragBusyRef.current || !plan || !days.includes(date) || date === item.placement.planned_date) return;
    if (!plan.placements.some((placement) => placement.id === item.placement.id && placement.task_id === item.placement.task_id && placement.planned_date === item.placement.planned_date)) {
      setDragError("The source placement changed. Refresh the weekly plan before trying again.");
      return;
    }
    if (duplicateDay(date, item)) {
      setDragError(`“${item.title}” is already planned for ${showDate(date)}. Both existing placements are kept. Choose another day.`);
      return;
    }
    setDragError(null);
    dragBusyRef.current = true;
    setDragBusy(true);
    try {
      await onRun(() => movePlacement(item.placement.id, date), `Moved “${item.title}” to ${showDate(date)}.`);
    } catch (caught) {
      setDragError(`${message(caught)} Refresh the weekly plan to check its saved state before retrying.`);
    } finally {
      dragBusyRef.current = false;
      setDragBusy(false);
    }
  }
  const dragControls: DragControls = {
    start: (event, placement, task) => {
      if (dragLocked || task.subtask_count > 0 || dragBusyRef.current) { event.preventDefault(); return; }
      event.dataTransfer.effectAllowed = "move";
      // Keep the source identity in this board, never trust an external drag payload.
      event.dataTransfer.setData("text/plain", task.title);
      const next = { placement, title: task.title };
      draggedRef.current = next;
      setDragged(next);
      // Keep in-flow feedback in place while the native gesture starts; removing
      // it here would move the source card underneath the pointer.
    },
    end: endDrag,
  };
  return (
    <section className={`weekly-planner${closed ? " weekly-planner-closed" : ""}`} aria-labelledby="planning-heading" aria-busy={loading}>
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
      {plan ? <>
        <div className="week-state">
          <strong className={`week-badge${closed ? " week-badge-closed" : ""}`}>{closed ? "Closed week · read-only history" : "Open week"}</strong>
          <p>{closed ? "At closure: " : "Weekly completion: "}{completed} of {total} work items complete ({total ? Math.round(completed / total * 100) : 0}%).</p>
        </div>
        {closed ? <p className="planning-hint muted">Saved {closed.closed_at ? new Date(closed.closed_at).toLocaleString() : "at closure"} · {closed.timezone}. Historical details and completion stay fixed. Current task status is shown separately. The project list edits current tasks.</p> : null}
        {plan.closed_weeks?.length ? <div className="closed-history field"><label htmlFor="closed-week-history">Closed-week history</label><select id="closed-week-history" value={closed ? plan.week_start : ""} disabled={loading || locked} onChange={(event) => { if (event.target.value) void navigate(event.target.value); }}>
          <option value="">Choose a closed week</option>
          {plan.closed_weeks.map((week) => <option key={week.week_start} value={week.week_start}>{showDate(week.week_start)} – {showDate(week.week_end)} · {week.completed}/{week.total} complete</option>)}
        </select></div> : null}
        <WeekActions key={plan.week_start} plan={plan} onRun={onRun} locked={locked || loading} />
      </> : null}
      {dragged ? <p className="drag-indicator" role="status"><strong>Move</strong> “{dragged.title}”{overDay ? ` · ${showDate(overDay)}` : " · drop on a highlighted day"}{overDay === dragged.placement.planned_date ? " · same day: no change" : overDay && duplicateDay(overDay) ? " · already planned here; choose another day" : ""}</p> : null}
      {dragBusy ? <p className="planning-hint muted" role="status">Saving planned date…</p> : null}
      {dragError ? <p role="alert" className="error">{dragError} <button type="button" className="link" disabled={loading || dragBusy} onClick={() => void refresh()}>Refresh weekly plan</button></p> : null}
      {error ? <p role="alert" className="error">{error} <button type="button" className="link" onClick={() => void refresh()}>Retry weekly plan</button></p> : null}
      {plan ? (
        <>
          <div className="day-selector" role="group" aria-label="Selected day">
            {days.map((date) => (
              <button key={date} type="button" className={`${selectedDay === date ? "day-choice day-choice-on" : "day-choice"}${destinationClass(date)}`} onDragOver={(event) => dragOver(event, date)} onDrop={(event) => void drop(event, date)} aria-pressed={selectedDay === date} onClick={() => setSelectedDay(date)}>
                <span>{dayName.format(plainDate(date)).slice(0, 3)}</span><span>{shortDate.format(plainDate(date))}</span>{date === plan.today ? <span className="today-mark">Today</span> : null}
              </button>
            ))}
          </div>
          <div className="week-board">
            {days.map((date) => {
              const placements = visiblePlacements.filter((placement) => placement.planned_date === date);
              return (
                <section key={date} className={`day-column${selectedDay === date ? " day-selected" : ""}${date === plan.today ? " day-today" : ""}${destinationClass(date)}`} onDragOver={(event) => dragOver(event, date)} onDrop={(event) => void drop(event, date)} aria-label={`${dayName.format(plainDate(date))}, ${showDate(date)}`}>
                  <h3>{dayName.format(plainDate(date))}<span>{shortDate.format(plainDate(date))}{date === plan.today ? " · Today" : ""}</span></h3>
                  {placements.length ? (
                    <ul className="day-placements">
                      {placements.map((placement) => {
                        if (closed) {
                          const historical = historicalTasks.get(placement.task_id);
                          const current = tasksById.get(placement.task_id);
                          if (!historical) return null;
                          return <li key={placement.id} className={`planned-card historical-card${historical.completed ? " planned-card-done" : ""}`}>
                            <WeekTaskDetails task={historical} context={historicalContext(historical)} />
                            <p className="historical-status">At closure: {historical.completed ? "Complete" : "Unfinished"}</p>
                            <p className="planned-meta muted">Current task: {current ? current.completed ? "Complete" : "Unfinished" : "No longer available"}</p>
                          </li>;
                        }
                        const task = tasksById.get(placement.task_id);
                        if (!task) return null;
                        const parent = task.parent_id ? tasksById.get(task.parent_id) : null;
                        const context = [projectById.get(task.project_id) ?? "Project", parent?.title].filter(Boolean).join(" / ");
                        return <PlannedCard key={placement.id} task={task} placement={placement} context={context} onRun={onRun} locked={locked || loading || dragBusy} onTrack={onTrack} drag={dragControls} />;
                      })}
                    </ul>
                  ) : <p className="empty-day muted">Nothing planned</p>}
                  <CalendarEvents events={events.filter((event) => event.first_day <= date && event.last_day >= date)} date={date} onRun={onRun} locked={locked || loading} />
                </section>
              );
            })}
          </div>
        </>
      ) : null}
    </section>
  );
}
