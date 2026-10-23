import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, getStatistics, type StatisticsState } from "./api";
import { Corrections } from "./Corrections";
import { savedDuration } from "./savedTime";

const dayLabel = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeZone: "UTC" });

export function Statistics({ visible }: { visible: boolean }) {
  const [showCorrections, setShowCorrections] = useState(false);
  const [state, setState] = useState<StatisticsState | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [projectId, setProjectId] = useState("");
  const request = useRef<AbortController | null>(null);
  const generation = useRef(0);
  const visibleRef = useRef(visible);
  visibleRef.current = visible;

  const refresh = useCallback(async () => {
    if (!visibleRef.current || document.visibilityState === "hidden") return;
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    const current = ++generation.current;
    setLoading(true);
    setError(null);
    try {
      const loaded = await getStatistics(controller.signal);
      if (!controller.signal.aborted && current === generation.current) setState(loaded);
    } catch (caught) {
      if (!controller.signal.aborted && current === generation.current) setError(caught instanceof ApiError && caught.status === 404
        ? "Statistics need the updated local service. Restart BearPlans, then use Refresh statistics."
        : `${caught instanceof ApiError ? caught.message : "Could not load statistics."} Use Refresh statistics to try again.`);
    } finally {
      if (!controller.signal.aborted && current === generation.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!visible) return;
    void refresh();
    const recheck = () => {
      if (document.visibilityState === "hidden") {
        request.current?.abort();
        generation.current += 1;
        setLoading(false);
      } else void refresh();
    };
    window.addEventListener("focus", recheck);
    document.addEventListener("visibilitychange", recheck);
    return () => {
      window.removeEventListener("focus", recheck);
      document.removeEventListener("visibilitychange", recheck);
      request.current?.abort();
      generation.current += 1;
    };
  }, [visible, refresh]);

  const tasks = state?.tasks.filter((task) => !projectId || task.project_id === projectId) ?? [];

  return <section hidden={!visible} className="statistics" aria-label="Statistics" aria-busy={loading}>
    <div className="forest-heading"><h2>Statistics</h2>
      <button type="button" className="link" disabled={loading} onClick={() => void refresh()}>Refresh statistics</button></div>
    {loading ? <p role="status" className="muted">Loading statistics…</p> : null}
    {error ? <p role="alert" className="error">{error}{state ? " Showing the last loaded statistics." : ""}</p> : null}
    {state ? <>
      <p className="muted">All-time saved work · Dates use {state.timezone}. Refresh to include work saved in another tab.</p>
      <dl className="stats-summary">
        <div><dt>Current leaf completion</dt><dd>{state.completion.completed} of {state.completion.total} complete ({state.completion.percent}%)</dd></div>
        <div><dt>Saved active time</dt><dd>{savedDuration(state.active_microseconds)}</dd></div>
        <div><dt>Saved sessions with intervals</dt><dd>{state.session_count}</dd></div>
      </dl>
      <p className="muted">Completion and estimates use current leaf tasks; parent containers are excluded. Saved time includes early finishes, resolved interruptions and earlier sessions. Running, paused, Needs review sessions, pauses and uncertain gaps are excluded.</p>
      <h3>By day</h3>
      <p className="muted">Only dates with saved intervals or current completions appear. Reopening a task removes its current completion; closed-week history stays frozen.</p>
      {state.days.length ? <ul className="stats-list" aria-label="Daily statistics">{state.days.map((day) => <li key={day.date}>
        <time dateTime={day.date}>{dayLabel.format(new Date(`${day.date}T00:00:00Z`))}</time>
        <span>{savedDuration(day.active_microseconds)}</span><span>{day.completed} completed</span>
      </li>)}</ul> : <p>No saved time or completed tasks yet.</p>}
      <h3>By project</h3>
      <p className="muted">Time belongs to the project recorded when tracking began. Task edits and removal do not erase saved work.</p>
      <ul className="stats-list" aria-label="Project statistics">{state.projects.map((project) => <li key={project.project_id}>
        <strong>{project.name}</strong><span>{savedDuration(project.active_microseconds)}</span>
        <span>{project.completion.completed} of {project.completion.total} complete ({project.completion.percent}%)</span>
      </li>)}</ul>
      <h3>Estimates and actual time</h3>
      <label className="stats-filter">Filter task details by project
        <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>
          <option value="">All projects</option>{state.projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.name}</option>)}
        </select>
      </label>
      <p className="muted">Compare each current leaf estimate with all its saved time. Missing estimates stay unspecified. Historical rows retain time but do not add current completion or estimates.</p>
      {tasks.length ? <ul className="stats-task-list" aria-label="Task statistics">{tasks.map((task) => <li key={`${task.project_id}:${task.task_id}`}>
        <span className="muted">{state.projects.find((project) => project.project_id === task.project_id)?.name}{task.parent_title ? ` / ${task.parent_title}` : ""}</span>
        <strong>{task.title}</strong>
        <span>{task.current_leaf ? task.completed ? "Complete" : "Incomplete" : "Historical work · no current leaf"}</span>
        <span>Estimate: {task.estimate_minutes === null ? "Not set" : `${task.estimate_minutes} min`}</span>
        <span>Actual: {savedDuration(task.active_microseconds)} · {task.session_count} saved {task.session_count === 1 ? "session" : "sessions"}</span>
      </li>)}</ul> : <p>No task details in this project.</p>}
    </> : null}
    <button type="button" aria-expanded={showCorrections} onClick={() => setShowCorrections((value) => !value)}>
      {showCorrections ? "Hide saved session corrections" : "Saved session corrections"}</button>
    {showCorrections ? <Corrections visible={visible} onApplied={() => void refresh()} /> : null}
  </section>;
}
