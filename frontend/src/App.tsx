import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { ApiError, TITLE_MAX_LENGTH, createTask, listTasks, type Task } from "./api";

type Load = { state: "loading" } | { state: "error"; message: string } | { state: "ready"; tasks: Task[] };

const savedAt = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" });

function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
}

export default function App() {
  const [load, setLoad] = useState<Load>({ state: "loading" });
  const [title, setTitle] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const listRequest = useRef<AbortController | null>(null);

  // Last request wins: a newer load cancels any older one still in flight.
  const refresh = useCallback(() => {
    listRequest.current?.abort();
    const controller = new AbortController();
    listRequest.current = controller;
    setLoad({ state: "loading" });
    listTasks(controller.signal)
      .then((tasks) => {
        if (!controller.signal.aborted) setLoad({ state: "ready", tasks });
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setLoad({ state: "error", message: errorMessage(error) });
      });
  }, []);

  useEffect(() => {
    refresh();
    return () => listRequest.current?.abort();
  }, [refresh]);

  const trimmed = title.trim();
  // Count characters (code points) as the service does, not UTF-16 units as maxLength would.
  const length = [...trimmed].length;
  const tooLong = length > TITLE_MAX_LENGTH;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!trimmed || tooLong || saving) return;
    setSaving(true);
    setSaveError(null);
    setStatus("");
    try {
      const task = await createTask(trimmed);
      if (load.state === "ready") {
        setLoad((current) => (current.state === "ready" ? { state: "ready", tasks: [...current.tasks, task] } : current));
      } else {
        refresh();
      }
      setTitle("");
      setStatus(`Saved “${task.title}”.`);
    } catch (error) {
      setSaveError(errorMessage(error));
    } finally {
      setSaving(false);
      inputRef.current?.focus();
    }
  }

  return (
    <main className="page">
      <header className="masthead">
        <h1>BearPlans</h1>
        <p className="tagline">Tasks saved on this computer</p>
      </header>

      <section className="card" aria-labelledby="new-task-heading">
        <h2 id="new-task-heading">New task</h2>
        <form className="entry" onSubmit={handleSubmit} noValidate>
          <label htmlFor="task-title" className="visually-hidden">
            Task title
          </label>
          <input
            id="task-title"
            ref={inputRef}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="e.g. Read chapter 4 for Math 55"
            autoComplete="off"
            autoFocus
            aria-invalid={saveError || tooLong ? true : undefined}
            aria-describedby={tooLong ? "task-limit" : saveError ? "task-error" : undefined}
          />
          <button type="submit" disabled={!trimmed || tooLong || saving}>
            {saving ? "Saving…" : "Add task"}
          </button>
        </form>
        <div className="message-slot">
          {tooLong && (
            <p id="task-limit" className="error">
              Keep the title to {TITLE_MAX_LENGTH} characters or fewer (currently {length}).
            </p>
          )}
          {saveError && (
            <p id="task-error" className="error" role="alert">
              {saveError}
            </p>
          )}
          <p className="status" role="status">
            {status}
          </p>
        </div>
      </section>

      <section className="card" aria-labelledby="saved-heading">
        <h2 id="saved-heading">
          Saved tasks
          {load.state === "ready" && (
            <>
              {" "}
              <span className="count">({load.tasks.length})</span>
            </>
          )}
        </h2>
        {load.state === "loading" && <p className="muted">Loading tasks…</p>}
        {load.state === "error" && (
          <div className="error-block" role="alert">
            <p className="error">{load.message}</p>
            <button type="button" className="secondary" onClick={() => refresh()}>
              Retry
            </button>
          </div>
        )}
        {load.state === "ready" &&
          (load.tasks.length === 0 ? (
            <p className="muted">No tasks yet. Add your first one above.</p>
          ) : (
            <ul className="tasks">
              {load.tasks.map((task) => (
                <li key={task.id}>
                  <span className="task-title">{task.title}</span>
                  <time className="muted" dateTime={task.created_at}>
                    {savedAt.format(new Date(task.created_at))}
                  </time>
                </li>
              ))}
            </ul>
          ))}
      </section>
    </main>
  );
}
