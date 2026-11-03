import { useCallback, useEffect, useState } from "react";
import { ApiError, connectGoogle, disconnectGoogle, getGoogle, syncGoogleTasks, type GoogleState } from "./api";

const stampLabel = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" });
const message = (caught: unknown, fallback: string) => caught instanceof ApiError ? caught.message : fallback;

export function Google({ visible, onChanged }: { visible: boolean; onChanged?: () => void }) {
  const [state, setState] = useState<GoogleState | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");

  const load = useCallback(async () => {
    try { setState(await getGoogle()); } catch (caught) { setError(message(caught, "Could not read the Google connection.")); }
  }, []);

  useEffect(() => { if (visible) void load(); }, [visible, load]);

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
      <p>{tasks.synced_tasks} tasks in {tasks.synced_lists} lists.
        {tasks.last_success_at ? ` Last synced ${stampLabel.format(new Date(tasks.last_success_at))}.` : " Not synced yet."}</p>
      {tasks.last_error ? <p role="alert" className="error">Last sync failed: {tasks.last_error}</p> : null}
      <p className="muted">BearPlans syncs every two minutes and shortly after each change.</p>
    </div> : null}
  </section>;
}
