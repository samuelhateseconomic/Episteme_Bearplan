import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, connectGoogle, disconnectGoogle, followGoogleCalendars, getGoogle, getGoogleCalendars, getGoogleChanges, refreshGoogleCalendars, syncGoogleTasks, type GoogleCalendar, type GoogleState } from "./api";

const stampLabel = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" });
const message = (caught: unknown, fallback: string) => caught instanceof ApiError ? caught.message : fallback;

export function Google({ visible, onChanged }: { visible: boolean; onChanged?: () => void }) {
  const [state, setState] = useState<GoogleState | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [calendars, setCalendars] = useState<GoogleCalendar[]>([]);
  const [chosen, setChosen] = useState<Set<string>>(new Set());
  const acceptCalendars = useCallback((list: GoogleCalendar[]) => {
    setCalendars(list);
    setChosen(new Set(list.filter((calendar) => calendar.followed).map((calendar) => calendar.calendar_id)));
  }, []);

  const load = useCallback(async () => {
    try { setState(await getGoogle()); } catch (caught) { setError(message(caught, "Could not read the Google connection.")); }
  }, []);

  useEffect(() => { if (visible) void load(); }, [visible, load]);

  // Calendars to read: show the saved list, and fetch it from Google the first time.
  const connected = state?.connected ?? false;
  useEffect(() => {
    if (!visible || !connected) return;
    void (async () => {
      try {
        const saved = await getGoogleCalendars();
        acceptCalendars(saved.length ? saved : await refreshGoogleCalendars());
      } catch (caught) { setError(message(caught, "Could not read your Google calendars.")); }
    })();
  }, [visible, connected, acceptCalendars]);

  // While sign-in is open in another tab, check every two seconds until it finishes.
  const pending = state?.sign_in_pending ?? false;
  useEffect(() => {
    if (!visible || !pending) return;
    const timer = window.setInterval(() => { void load(); }, 2000);
    return () => window.clearInterval(timer);
  }, [visible, pending, load]);

  const run = async (label: string, action: () => Promise<GoogleState | void>, done = "") => {
    setBusy(label);
    setError(null);
    setStatus("");
    try {
      const next = await action();
      if (next) setState(next);
      if (done) setStatus(done);
    } catch (caught) {
      setError(message(caught, "Something went wrong. Nothing was changed."));
      await load();
    } finally {
      setBusy(null);
    }
  };

  const connect = () => run("connect", async () => {
    const { url } = await connectGoogle();
    window.open(url, "_blank", "noopener");
    setStatus("Google sign-in opened in a new tab. Approve every permission there, then come back here.");
    return getGoogle();
  });
  const sync = () => run("sync", async () => {
    const next = await syncGoogleTasks();
    onChanged?.();
    return next;
  }, "Google Tasks is up to date.");

  const tasks = state?.tasks;
  return <section hidden={!visible} className="google" aria-label="Google" aria-busy={busy !== null}>
    <div className="forest-heading"><h2>Google</h2>
      <button type="button" disabled={busy !== null || !state?.connected} onClick={() => void sync()}>
        {busy === "sync" ? "Syncing…" : "Sync now"}</button>
    </div>
    <p className="muted">Every project, task and subtask is copied to Google Tasks: each project becomes a list with the same name. Ticking a task done in Google marks it done here too. Other changes made in Google are replaced by BearPlans. Your own Google lists are never touched.</p>
    {error ? <p role="alert" className="error">{error}</p> : null}
    {status ? <p role="status">{status}</p> : null}

    {state && !state.configured ? <p className="google-setup">No Google sign-in file was found. Save your Desktop app credential as <code>.secrets/google_oauth_client.json</code>, then reload this page.</p> : null}
    {state?.configured ? <div className="google-connection">
      <p>{state.connected ? "Connected to Google." : state.sign_in_pending ? "Waiting for you to finish signing in…" : "Not connected."}</p>
      {state.sign_in_error ? <p role="alert" className="error">{state.sign_in_error}</p> : null}
      {state.missing_permissions.length ? <p role="alert" className="error">Some permissions were not given ({state.missing_permissions.join(", ")}). Choose Reconnect Google and tick every box.</p> : null}
      <button type="button" disabled={busy !== null} onClick={() => void connect()}>{state.connected ? "Reconnect Google" : "Connect Google"}</button>
      {state.connected ? <button type="button" className="link" disabled={busy !== null}
        onClick={() => void run("disconnect", disconnectGoogle, "Disconnected. Your Google lists stay as they are.")}>Disconnect</button> : null}
    </div> : null}

    {tasks && state?.connected ? <div className="google-tasks">
      <h3>Google Tasks</h3>
      <p>{tasks.synced_tasks} {tasks.synced_tasks === 1 ? "task" : "tasks"} in {tasks.synced_lists} {tasks.synced_lists === 1 ? "list" : "lists"}.
        {tasks.last_success_at ? ` Last synced ${stampLabel.format(new Date(tasks.last_success_at))}.` : " Not synced yet."}</p>
      {tasks.last_error ? <p role="alert" className="error">Last sync failed: {tasks.last_error}</p> : null}
      <h3>Google Calendar</h3>
      <p>{tasks.synced_events} upcoming {tasks.synced_events === 1 ? "event" : "events"} in the “BearPlans” calendar.</p>
      <p className="muted">Give a planned task a start time (open it on the Plan screen, then “Move or remove”) and it appears in the BearPlans calendar with a reminder 30 minutes before. Finishing the task removes the event.</p>
      <p className="muted">BearPlans syncs every two minutes and shortly after each change.</p>
    </div> : null}

    {state?.connected ? <div className="google-calendars">
      <h3>Calendars to show</h3>
      <p className="muted">Events from the calendars you tick appear beside each day on the Plan screen, where any event can be added as a task. BearPlans only reads these calendars; it never changes them.</p>
      {calendars.length ? <fieldset>
        <legend>Choose the calendars whose events you want to see</legend>
        {calendars.map((calendar) => <label key={calendar.calendar_id}>
          <input type="checkbox" checked={chosen.has(calendar.calendar_id)} onChange={(event) => setChosen((current) => {
            const next = new Set(current);
            if (event.target.checked) next.add(calendar.calendar_id); else next.delete(calendar.calendar_id);
            return next;
          })} />
          {calendar.color ? <span className="calendar-swatch" style={{ background: calendar.color }} aria-hidden="true" /> : null}
          {calendar.summary}{calendar.is_primary ? <span className="muted"> · main calendar</span> : null}
        </label>)}
      </fieldset> : <p className="muted">No calendars found yet.</p>}
      <div className="form-actions">
        <button type="button" disabled={busy !== null || !calendars.length} onClick={() => void run("follow", async () => {
          acceptCalendars(await followGoogleCalendars([...chosen]));
          onChanged?.();
        }, "Saved your calendars. Their events now appear on the Plan screen.")}>{busy === "follow" ? "Saving…" : "Save calendars"}</button>
        <button type="button" className="link" disabled={busy !== null} onClick={() => void run("calendars", async () => {
          acceptCalendars(await refreshGoogleCalendars());
        }, "Updated your calendar list and events.")}>Refresh calendars</button>
      </div>
    </div> : null}
  </section>;
}

const CHANGE_CHECK_MS = 30000;

/** Calls onChange when a background Google sync changed something the page shows
 * (a task ticked in Google, followed-calendar events). Checks every 30 seconds while
 * the page is visible and when the window regains focus; never at mount. */
export function useGoogleChanges(onChange: () => void) {
  const seen = useRef<number | null>(null);
  const callback = useRef(onChange);
  callback.current = onChange;
  useEffect(() => {
    let stopped = false;
    const check = async () => {
      if (document.visibilityState === "hidden") return;
      try {
        const { version } = await getGoogleChanges();
        if (stopped) return;
        if (seen.current !== null && version !== seen.current) callback.current();
        seen.current = version;
      } catch { /* not connected or offline: try again later */ }
    };
    const timer = window.setInterval(() => { void check(); }, CHANGE_CHECK_MS);
    const onFocus = () => { void check(); };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onFocus);
    return () => {
      stopped = true;
      window.clearInterval(timer);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onFocus);
    };
  }, []);
}
