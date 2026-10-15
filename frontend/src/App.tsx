import { useCallback, useEffect, useId, useRef, useState, type FormEvent, type ReactNode } from "react";
import {
  ApiError,
  ESTIMATE_MAX_MINUTES,
  ESTIMATE_MIN_MINUTES,
  NAME_MAX_LENGTH,
  TITLE_MAX_LENGTH,
  createProject,
  createTask,
  listProjects,
  listTasks,
  renameProject,
  removeSubtask,
  setTaskCompletion,
  updateTask,
  type Project,
  type Task,
  type TaskEdit,
} from "./api";
import { TaskPlanning, WeeklyPlanner, usePlanning } from "./WeeklyPlanner";

const dueOn = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeZone: "UTC" });

function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
}

/** A deadline is a plain date; parse it as UTC so it never shifts a day in local time. */
function formatDeadline(deadline: string): string {
  return dueOn.format(new Date(`${deadline}T00:00:00Z`));
}

function formatEstimate(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest ? `${hours} h ${rest} min` : `${hours} h`;
}

export default function App() {
  const planning = usePlanning();
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [tasks, setTasks] = useState<Task[] | null>(null);
  const [progress, setProgress] = useState<{ completed: number; total: number } | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [addingSubtaskTo, setAddingSubtaskTo] = useState<string | null>(null);
  const [renaming, setRenaming] = useState(false);
  const [mutations, setMutations] = useState(0);
  const taskRequest = useRef<AbortController | null>(null);
  // Handlers capture the project that was selected when they were created. A mutation
  // can resolve after the user has moved on, so the refresh needs the current project,
  // not the captured one.
  const selectedIdRef = useRef<string | null>(null);
  selectedIdRef.current = selectedId;

  const selected = projects?.find((p) => p.id === selectedId) ?? null;

  const loadProjects = useCallback(() => {
    setLoadError(null);
    return listProjects()
      .then((loaded) => {
        setProjects(loaded);
        setSelectedId((current) => current ?? loaded[0]?.id ?? null);
      })
      .catch((error: unknown) => setLoadError(errorMessage(error)));
  }, []);

  useEffect(() => {
    void loadProjects();
  }, [loadProjects]);


  // Completion of a parent is derived from its subtasks, so after any change the
  // service is the only thing that knows the right answer. Always re-read.
  const refreshTasks = useCallback((projectId: string) => {
    taskRequest.current?.abort();
    const controller = new AbortController();
    taskRequest.current = controller;
    return listTasks(projectId, controller.signal)
      .then((loaded) => {
        // Drop a late response for a project the user has already left, or its tasks
        // would appear under another project's heading.
        if (controller.signal.aborted || selectedIdRef.current !== projectId) return true;
        setTasks(loaded.tasks);
        setProgress(loaded.progress);
        setLoadError(null);
        return true;
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setLoadError(errorMessage(error));
        return controller.signal.aborted;
      });
  }, []);

  // Either load can be the one that failed, and selecting the same project again does
  // not re-run the effect, so a retry has to refetch both.
  const retry = useCallback(async () => {
    await loadProjects();
    const current = selectedIdRef.current;
    if (current) await refreshTasks(current);
  }, [loadProjects, refreshTasks]);

  useEffect(() => {
    // Any open form belongs to the project that was selected when it opened, so
    // close them here rather than in one button's handler.
    setEditing(null);
    setAddingSubtaskTo(null);
    setRenaming(false);
    if (!selectedId) return;
    setTasks(null);
    setProgress(null);
    refreshTasks(selectedId);
    return () => taskRequest.current?.abort();
  }, [selectedId, refreshTasks]);

  async function run(work: () => Promise<unknown>, done: string) {
    setMutations((count) => count + 1);
    try {
      await work();
      const current = selectedIdRef.current;
      const refreshed = await Promise.all([current ? refreshTasks(current) : Promise.resolve(true), planning.refresh()]);
      setStatus(refreshed.every(Boolean) ? done : "Saved. Some views could not refresh. Use the retry controls to see the saved changes.");
    } finally {
      setMutations((count) => count - 1);
    }
  }

  const parents = tasks?.filter((task) => task.parent_id === null) ?? [];
  const subtasksOf = (id: string) => tasks?.filter((task) => task.parent_id === id) ?? [];

  return (
    <main className="page">
      <header className="page-head">
        <h1>BearPlans</h1>
        <p className="muted">Make room for your week.</p>
      </header>

      {loadError ? (
        <p className="error load-error" role="alert">
          {loadError}{" "}
          <button type="button" className="link" onClick={() => void retry()}>
            Try again
          </button>
        </p>
      ) : null}

      <div className="workspace">
        <div className="work-list">
          <section className="projects" aria-labelledby="projects-heading">
            <h2 id="projects-heading">Projects</h2>
            {projects === null && !loadError ? <p className="muted">Loading…</p> : null}
            {projects !== null ? (
              <>
                <ul className="project-list">
                  {projects.map((project) => (
                    <li key={project.id}>
                      <button
                        type="button"
                        className={project.id === selectedId ? "chip chip-on" : "chip"}
                        aria-current={project.id === selectedId ? "true" : undefined}
                        onClick={() => setSelectedId(project.id)}
                      >
                        {project.name}
                      </button>
                    </li>
                  ))}
                </ul>

                <div className="project-actions">
                  <TextForm
                    label="New project"
                    placeholder="Add a project"
                    submitLabel="Add project"
                    maxLength={NAME_MAX_LENGTH}
                    onSubmit={async (name) => {
                      const project = await createProject(name);
                      setProjects((current) => [...(current ?? []), project]);
                      setSelectedId(project.id);
                      setStatus(`Added project “${project.name}”.`);
                    }}
                  />
                  {selected ? (
                    renaming ? (
                      <TextForm
                        key={`rename-${selected.id}-${selected.revision}`}
                        label={`Rename “${selected.name}”`}
                        placeholder="New name"
                        submitLabel="Save name"
                        initial={selected.name}
                        maxLength={NAME_MAX_LENGTH}
                        onCancel={() => setRenaming(false)}
                        onSubmit={async (name) => {
                          const updated = await renameProject(selected.id, name);
                          setProjects((current) => (current ?? []).map((p) => (p.id === updated.id ? updated : p)));
                          setRenaming(false);
                          setStatus(`Renamed to “${updated.name}”.`);
                        }}
                      />
                    ) : (
                      <button type="button" className="link" onClick={() => setRenaming(true)}>
                        Rename “{selected.name}”
                      </button>
                    )
                  ) : null}
                </div>
              </>
            ) : null}
          </section>

          {selected ? (
            <section className="tasks-section" aria-labelledby="tasks-heading">
              <h2 id="tasks-heading">{selected.name}</h2>
              {progress ? <p className="muted">{progress.completed} of {progress.total} work items complete</p> : null}

              <TaskForm
                key={`new-task-${selected.id}`}
                submitLabel="Add task"
                onSubmit={(edit) => run(() => createTask({ ...edit, title: edit.title ?? "", project_id: selected.id }), "Task added.")}
              />

              {tasks === null && !loadError ? <p className="muted">Loading…</p> : null}
              {tasks !== null && parents.length === 0 ? <p className="muted">No tasks in this project yet.</p> : null}

              <ul className="tasks">
                {parents.map((task) => {
                  const children = subtasksOf(task.id);
                  return (
                    <li key={task.id} className="task">
                      <TaskRow
                        task={task}
                        onToggle={(complete) =>
                          run(() => setTaskCompletion(task.id, complete), complete ? "Marked complete." : "Reopened.")
                        }
                        onEdit={() => setEditing(editing === task.id ? null : task.id)}
                        editing={editing === task.id}
                        locked={mutations > 0 || Boolean(loadError) || Boolean(planning.error)}
                        planning={<TaskPlanning task={task} plan={planning.plan} selectedDay={planning.selectedDay} onRun={run} />}
                        extra={
                          <button type="button" className="link" onClick={() => setAddingSubtaskTo(addingSubtaskTo === task.id ? null : task.id)}>
                            {addingSubtaskTo === task.id ? "Cancel subtask" : "Add subtask"}
                          </button>
                        }
                      />

                      {editing === task.id ? (
                        <TaskForm
                          task={task}
                          submitLabel="Save changes"
                          onCancel={() => setEditing(null)}
                          onSubmit={async (edit) => {
                            await run(() => updateTask(task.id, edit), "Changes saved.");
                            setEditing(null);
                          }}
                        />
                      ) : null}

                      {addingSubtaskTo === task.id ? (
                        <TaskForm
                          submitLabel="Add subtask"
                          onCancel={() => setAddingSubtaskTo(null)}
                          onSubmit={async (edit) => {
                            await run(() => createTask({ ...edit, title: edit.title ?? "", parent_id: task.id }), "Subtask added.");
                            setAddingSubtaskTo(null);
                          }}
                        />
                      ) : null}

                      {children.length ? (
                        <ul className="subtasks">
                          {children.map((child) => (
                            <li key={child.id} className="task">
                              <TaskRow
                                task={child}
                                onToggle={(complete) =>
                                  run(() => setTaskCompletion(child.id, complete), complete ? "Marked complete." : "Reopened.")
                                }
                                onEdit={() => setEditing(editing === child.id ? null : child.id)}
                                editing={editing === child.id}
                                locked={mutations > 0 || Boolean(loadError) || Boolean(planning.error)}
                                planning={<TaskPlanning task={child} plan={planning.plan} selectedDay={planning.selectedDay} onRun={run} />}
                              />
                              {editing === child.id ? (
                                <TaskForm
                                  task={child}
                                  submitLabel="Save changes"
                                  onRemove={async () => {
                                    await run(() => removeSubtask(child.id), "Subtask removed.");
                                    setEditing(null);
                                  }}
                                  onCancel={() => setEditing(null)}
                                  onSubmit={async (edit) => {
                                    await run(() => updateTask(child.id, edit), "Changes saved.");
                                    setEditing(null);
                                  }}
                                />
                              ) : null}
                            </li>
                          ))}
                        </ul>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            </section>
          ) : null}
        </div>
      <WeeklyPlanner state={planning} projects={projects ?? []} onRun={run} locked={mutations > 0 || planning.loading || Boolean(loadError) || Boolean(planning.error)} />
      </div>

      <p className="status" role="status" aria-live="polite">{status}</p>
    </main>
  );
}

function TaskRow({
  task,
  onToggle,
  onEdit,
  editing,
  extra,
  planning,
  locked,
}: {
  task: Task;
  onToggle: (complete: boolean) => Promise<void>;
  onEdit: () => void;
  editing: boolean;
  extra?: ReactNode;
  planning?: ReactNode;
  locked: boolean;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const derived = task.subtask_count > 0;
  const hint = derived
    ? `Complete when all ${task.subtask_count} subtasks are. ${task.completed_subtask_count} of ${task.subtask_count} done.`
    : undefined;

  return (
    <div className={task.completed ? "task-row task-done" : "task-row"}>
      <input
        type="checkbox"
        id={`done-${task.id}`}
        checked={task.completed}
        disabled={derived || busy || locked}
        title={hint}
        aria-describedby={derived ? `derived-${task.id}` : undefined}
        onChange={async (event) => {
          setBusy(true);
          setError(null);
          try {
            await onToggle(event.target.checked);
          } catch (caught) {
            setError(errorMessage(caught));
          } finally {
            setBusy(false);
          }
        }}
      />
      <div className="task-main">
        <label htmlFor={`done-${task.id}`} className="task-title">{task.title}</label>
        <p className="task-meta muted">
          {derived ? (
            <span id={`derived-${task.id}`}>{task.completed_subtask_count} of {task.subtask_count} subtasks done</span>
          ) : null}
          {task.deadline ? <span>Due {formatDeadline(task.deadline)}</span> : null}
          {task.estimate_minutes ? <span>{formatEstimate(task.estimate_minutes)}</span> : null}
        </p>
        {task.notes ? <p className="task-notes">{task.notes}</p> : null}
        {planning}
        {error ? <p className="error" role="alert">{error}</p> : null}
      </div>
      <div className="task-actions">
        <button type="button" className="link" onClick={onEdit}>{editing ? "Cancel" : "Edit"}</button>
        {extra}
      </div>
    </div>
  );
}

/** Create or edit a task. Submits only the fields the form actually carries. */
function TaskForm({
  task,
  submitLabel,
  onSubmit,
  onCancel,
  onRemove,
}: {
  task?: Task;
  submitLabel: string;
  onSubmit: (edit: TaskEdit & { title?: string }) => Promise<void>;
  onCancel?: () => void;
  onRemove?: () => Promise<void>;
}) {
  const [title, setTitle] = useState(task?.title ?? "");
  const [notes, setNotes] = useState(task?.notes ?? "");
  const [deadline, setDeadline] = useState(task?.deadline ?? "");
  const [estimate, setEstimate] = useState(task?.estimate_minutes ? String(task.estimate_minutes) : "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmRemoval, setConfirmRemoval] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);
  // Several of these forms can be open at once, so ids must be unique per instance.
  const uid = useId();

  const trimmed = title.trim();
  // Count code points, as the service does, not the UTF-16 units maxLength would.
  const tooLong = [...trimmed].length > TITLE_MAX_LENGTH;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!trimmed || tooLong || busy) return;
    setBusy(true);
    setError(null);
    try {
      const estimateText = estimate.trim();
      const estimateNumber = Number(estimateText);
      await onSubmit({
        title: trimmed,
        notes: notes.trim() || null,
        deadline: deadline.trim() || null,
        // Empty clears the field. Anything that is not a whole number is passed through
        // unchanged so the service rejects it by name, rather than becoming JSON null
        // here and silently clearing the estimate instead.
        estimate_minutes:
          estimateText === ""
            ? null
            : Number.isInteger(estimateNumber)
              ? estimateNumber
              : (estimateText as unknown as number),
      });
      if (!task) {
        setTitle("");
        setNotes("");
        setDeadline("");
        setEstimate("");
        titleRef.current?.focus();
      }
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="task-form" onSubmit={handleSubmit}>
      <div className="field">
        <label htmlFor={`title-${uid}`}>Title</label>
        <input
          id={`title-${uid}`}
          ref={titleRef}
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          aria-invalid={tooLong || error ? true : undefined}
          required
        />
      </div>
      <div className="field-row">
        <div className="field">
          <label htmlFor={`deadline-${uid}`}>Deadline</label>
          <input
            id={`deadline-${uid}`}
            type="date"
            value={deadline}
            onChange={(event) => setDeadline(event.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor={`estimate-${uid}`}>Estimate (minutes)</label>
          <input
            id={`estimate-${uid}`}
            type="number"
            inputMode="numeric"
            min={ESTIMATE_MIN_MINUTES}
            max={ESTIMATE_MAX_MINUTES}
            value={estimate}
            onChange={(event) => setEstimate(event.target.value)}
          />
        </div>
      </div>
      <div className="field">
        <label htmlFor={`notes-${uid}`}>Notes</label>
        <textarea
          id={`notes-${uid}`}
          rows={2}
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
        />
      </div>
      {tooLong ? <p className="error">Keep the title to {TITLE_MAX_LENGTH} characters or fewer.</p> : null}
      {error ? <p className="error" role="alert">{error}</p> : null}
      <div className="form-actions">
        <button type="submit" disabled={!trimmed || tooLong || busy}>{busy ? "Saving…" : submitLabel}</button>
        {onCancel ? <button type="button" className="link" onClick={onCancel}>Cancel</button> : null}
        {onRemove ? (
          <button type="button" className="link" disabled={busy} onClick={() => setConfirmRemoval(true)}>
            Remove subtask
          </button>
        ) : null}
      </div>
      {confirmRemoval && onRemove ? (
        <div>
          <p>Remove this subtask permanently? Removing the last subtask leaves its parent incomplete.</p>
          <button type="button" disabled={busy} onClick={async () => {
            setBusy(true);
            setError(null);
            try { await onRemove(); }
            catch (caught) { setError(errorMessage(caught)); }
            finally { setBusy(false); }
          }}>Confirm removal</button>{" "}
          <button type="button" className="link" disabled={busy} onClick={() => setConfirmRemoval(false)}>Keep subtask</button>
        </div>
      ) : null}
    </form>
  );
}

/** A one-field form, used for creating and renaming projects. */
function TextForm({
  label,
  placeholder,
  submitLabel,
  initial = "",
  maxLength,
  onSubmit,
  onCancel,
}: {
  label: string;
  placeholder: string;
  submitLabel: string;
  initial?: string;
  maxLength: number;
  onSubmit: (value: string) => Promise<void>;
  onCancel?: () => void;
}) {
  const [value, setValue] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const trimmed = value.trim();
  const tooLong = [...trimmed].length > maxLength;
  const id = useId();

  return (
    <form
      className="text-form"
      onSubmit={async (event) => {
        event.preventDefault();
        if (!trimmed || tooLong || busy) return;
        setBusy(true);
        setError(null);
        try {
          await onSubmit(trimmed);
          if (!initial) setValue("");
        } catch (caught) {
          setError(errorMessage(caught));
        } finally {
          setBusy(false);
        }
      }}
    >
      <label htmlFor={id}>{label}</label>
      <div className="field-row">
        <input id={id} value={value} placeholder={placeholder} maxLength={maxLength * 2} onChange={(event) => setValue(event.target.value)} />
        <button type="submit" disabled={!trimmed || tooLong || busy}>{submitLabel}</button>
        {onCancel ? <button type="button" className="link" onClick={onCancel}>Cancel</button> : null}
      </div>
      {tooLong ? <p className="error">Keep this to {maxLength} characters or fewer.</p> : null}
      {error ? <p className="error" role="alert">{error}</p> : null}
    </form>
  );
}
