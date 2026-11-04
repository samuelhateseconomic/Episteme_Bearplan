import { useCallback, useEffect, useRef, useState } from "react";
import {
  ApiError, addBCoursesAssignment, dismissBCoursesAssignment, followBCourses, getBCourses, refreshBCourses,
  resolveBCoursesDueDate, type BCoursesAssignment, type BCoursesState,
} from "./api";

const dueLabel = new Intl.DateTimeFormat(undefined, { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
const dayLabel = new Intl.DateTimeFormat(undefined, { weekday: "short", month: "short", day: "numeric", timeZone: "UTC" });
const stampLabel = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" });

const day = (iso: string) => dayLabel.format(new Date(`${iso}T00:00:00Z`));
const message = (caught: unknown, fallback: string) => caught instanceof ApiError ? caught.message : fallback;

function Item({ item, children }: { item: BCoursesAssignment; children?: React.ReactNode }) {
  return <li className="bcourses-item">
    <div className="bcourses-item-text">
      <strong>{item.title}</strong>
      <span className="muted">{item.course_name}</span>
      <span>{item.due_at ? `Due ${dueLabel.format(new Date(item.due_at))}` : "No due date"}
        {item.points_possible != null ? ` · ${item.points_possible} pts` : ""}
        {!item.in_source ? " · No longer listed in bCourses" : ""}</span>
      {item.html_url ? <a href={item.html_url} target="_blank" rel="noreferrer noopener">Open in bCourses</a> : null}
    </div>
    {children ? <div className="bcourses-item-actions">{children}</div> : null}
  </li>;
}

export function BCourses({ visible, onChanged }: { visible: boolean; onChanged?: () => void }) {
  const [state, setState] = useState<BCoursesState | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [chosen, setChosen] = useState<Set<string>>(new Set());
  const loaded = useRef(false);

  const accept = useCallback((next: BCoursesState) => {
    setState(next);
    setChosen(new Set(next.courses.filter((course) => course.followed).map((course) => course.course_id)));
  }, []);

  const run = useCallback(async (label: string, action: () => Promise<BCoursesState | void>, done = "") => {
    setBusy(label);
    setError(null);
    setStatus("");
    try {
      const next = await action();
      if (next) accept(next);
      if (done) setStatus(done);
    } catch (caught) {
      setError(message(caught, "Something went wrong. Nothing was changed."));
      // The service records failed refreshes; show its saved state too.
      try { accept(await getBCourses()); } catch { /* keep the current view */ }
    } finally {
      setBusy(null);
    }
  }, [accept]);

  useEffect(() => {
    if (!visible || loaded.current) return;
    loaded.current = true;
    void run("load", async () => {
      const first = await getBCourses();
      // First visit with a token: fetch the course list so courses can be chosen.
      return first.configured && !first.sync.last_attempt_at ? refreshBCourses() : first;
    });
  }, [visible, run]);

  const followed = state?.courses.filter((course) => course.followed) ?? [];
  const now = Date.now();
  const items = state?.assignments ?? [];
  const changed = items.filter((item) => item.status === "added" && item.due_changed);
  const fresh = items.filter((item) => item.status === "new");
  const upcoming = fresh.filter((item) => item.due_at && new Date(item.due_at).getTime() >= now);
  const undated = fresh.filter((item) => !item.due_at);
  const past = fresh.filter((item) => item.due_at && new Date(item.due_at).getTime() < now).reverse();
  const added = items.filter((item) => item.status === "added");
  const dismissed = items.filter((item) => item.status === "dismissed");

  const add = (item: BCoursesAssignment) => run(`add:${item.assignment_id}`, async () => {
    const result = await addBCoursesAssignment(item.assignment_id);
    onChanged?.();
    setStatus(`Added “${result.task.title}” to ${item.course_name}${result.task.deadline ? `, due ${day(result.task.deadline)}` : ""}.`);
    return getBCourses();
  });
  const dismiss = (item: BCoursesAssignment, value: boolean) => run(`dismiss:${item.assignment_id}`, async () => {
    await dismissBCoursesAssignment(item.assignment_id, value);
    return getBCourses();
  }, value ? `Dismissed “${item.title}”.` : `Restored “${item.title}”.`);
  const resolve = (item: BCoursesAssignment, useNew: boolean) => run(`due:${item.assignment_id}`, async () => {
    await resolveBCoursesDueDate(item.assignment_id, useNew);
    if (useNew) onChanged?.();
    return getBCourses();
  }, useNew ? `Updated the due date of “${item.title}”.` : `Kept your due date for “${item.title}”.`);

  const actions = (item: BCoursesAssignment) => <>
    <button type="button" disabled={busy !== null} onClick={() => void add(item)} aria-label={`Add “${item.title}” as a task`}>Add</button>
    <button type="button" className="link" disabled={busy !== null} onClick={() => void dismiss(item, true)} aria-label={`Dismiss “${item.title}”`}>Dismiss</button>
  </>;
  const list = (label: string, entries: BCoursesAssignment[]) => <ul className="bcourses-list" aria-label={label}>
    {entries.map((item) => <Item key={item.assignment_id} item={item}>{actions(item)}</Item>)}
  </ul>;

  return <section hidden={!visible} className="bcourses" aria-label="bCourses" aria-busy={busy !== null}>
    <div className="forest-heading"><h2>bCourses</h2>
      <button type="button" disabled={busy !== null || !state?.configured} onClick={() => void run("refresh", refreshBCourses, "Updated from bCourses.")}>
        {busy === "refresh" ? "Refreshing…" : "Refresh"}</button>
    </div>
    <p className="muted">Assignments from the courses you follow wait here. Nothing becomes a task until you choose Add. BearPlans only reads bCourses; it never changes anything there.</p>
    {state?.sync.last_success_at ? <p className="muted">Last updated {stampLabel.format(new Date(state.sync.last_success_at))}.</p> : null}
    {error ? <p role="alert" className="error">{error}</p> : null}
    {status ? <p role="status">{status}</p> : null}
    {state && !state.configured ? <p className="bcourses-setup">No bCourses token is set. In bCourses, open Account → Settings → New Access Token. Paste the token after <code>BCOURSES_TOKEN=</code> in <code>bearplans.secrets.env</code> in the BearPlans secrets folder (<code>~/Library/Application Support/BearPlans/secrets/</code>), save the file, then reload this page.</p> : null}

    {state?.courses.length ? <details className="bcourses-courses" open={followed.length === 0}>
      <summary>Courses to follow ({followed.length} of {state.courses.filter((course) => course.in_source).length})</summary>
      <fieldset>
        <legend>Choose the courses whose assignments you want to see</legend>
        {state.courses.filter((course) => course.in_source || course.followed).map((course) => <label key={course.course_id}>
          <input type="checkbox" checked={chosen.has(course.course_id)} onChange={(event) => setChosen((current) => {
            const next = new Set(current);
            if (event.target.checked) next.add(course.course_id); else next.delete(course.course_id);
            return next;
          })} />
          {course.name}{course.term ? <span className="muted"> · {course.term}</span> : null}
        </label>)}
      </fieldset>
      <button type="button" disabled={busy !== null} onClick={() => void run("follow", () => followBCourses([...chosen]), "Saved your courses and updated assignments.")}>
        {busy === "follow" ? "Saving…" : "Save courses"}</button>
    </details> : null}

    {changed.length ? <>
      <h3>Due date changed in bCourses</h3>
      <ul className="bcourses-list" aria-label="Due date changed">
        {changed.map((item) => <Item key={item.assignment_id} item={item}>
          <span>Your task: {item.accepted_due_date ? day(item.accepted_due_date) : "no due date"} → bCourses: {item.due_date ? day(item.due_date) : "no due date"}</span>
          <button type="button" disabled={busy !== null} onClick={() => void resolve(item, true)}>Use new due date</button>
          <button type="button" className="link" disabled={busy !== null} onClick={() => void resolve(item, false)}>Keep mine</button>
        </Item>)}
      </ul>
    </> : null}

    {followed.length ? <>
      <h3>Upcoming ({upcoming.length})</h3>
      {upcoming.length ? list("Upcoming assignments", upcoming) : <p className="muted">No new upcoming assignments.</p>}
      <h3>No due date ({undated.length})</h3>
      {undated.length ? list("Assignments with no due date", undated) : <p className="muted">None.</p>}
      {past.length ? <details><summary>Past due, not added ({past.length})</summary>{list("Past due assignments", past)}</details> : null}
      {added.length ? <details><summary>Added as tasks ({added.length})</summary>
        <ul className="bcourses-list" aria-label="Added assignments">{added.map((item) => <Item key={item.assignment_id} item={item} />)}</ul></details> : null}
      {dismissed.length ? <details><summary>Dismissed ({dismissed.length})</summary>
        <ul className="bcourses-list" aria-label="Dismissed assignments">{dismissed.map((item) => <Item key={item.assignment_id} item={item}>
          <button type="button" className="link" disabled={busy !== null} onClick={() => void dismiss(item, false)}>Restore</button>
        </Item>)}</ul></details> : null}
    </> : state?.courses.length ? <p className="muted">Choose at least one course above, then Save courses.</p> : null}
  </section>;
}
