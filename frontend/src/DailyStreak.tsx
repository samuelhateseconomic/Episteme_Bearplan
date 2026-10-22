import { useCallback, useEffect, useId, useRef, useState } from "react";
import { ApiError, getStreaks, type StreakState } from "./api";

// Service dates are calendar dates. UTC formatting prevents the browser's zone
// from shifting them, including when the browser and service are on different days.
const dayLabel = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", timeZone: "UTC" });
const weekdayLabel = new Intl.DateTimeFormat(undefined, { weekday: "short", timeZone: "UTC" });
const asDate = (date: string) => new Date(`${date}T00:00:00Z`);

function savedTime(microseconds: number): string {
  const seconds = Math.floor(microseconds / 1_000_000);
  return `${Math.floor(seconds / 60)} min ${String(seconds % 60).padStart(2, "0")} s`;
}

export function DailyStreak({ visible, lastSessionId }: { visible: boolean; lastSessionId: string | null }) {
  const [state, setState] = useState<StreakState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const request = useRef<AbortController | null>(null);
  const generation = useRef(0);
  const visibleRef = useRef(visible);
  visibleRef.current = visible;
  const progressId = useId();

  const refresh = useCallback(async () => {
    if (!visibleRef.current || document.visibilityState === "hidden") return;
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    const current = ++generation.current;
    setLoading(true);
    setError(null);
    try {
      const loaded = await getStreaks(controller.signal);
      if (!controller.signal.aborted && current === generation.current) setState(loaded);
    } catch (caught) {
      if (!controller.signal.aborted && current === generation.current) setError(caught instanceof ApiError && caught.status === 404
        ? "Daily streaks need the updated local service. Restart BearPlans, then use Refresh streak."
        : `${caught instanceof ApiError ? caught.message : "Could not load your daily streak."} Use Refresh streak to try again.`);
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
    // Re-read the service's calendar day across midnight while Track stays open.
    const interval = window.setInterval(() => void refresh(), 60_000);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener("focus", recheck);
      document.removeEventListener("visibilitychange", recheck);
      request.current?.abort();
      generation.current += 1;
    };
  }, [visible, lastSessionId, refresh]);

  const today = state?.days.find((day) => day.date === state.today);
  const active = today?.active_microseconds ?? 0;

  return <section className="daily-streak" aria-label="Daily streak" aria-busy={loading}>
    <div className="forest-heading">
      <h3>Daily streak</h3>
      <button type="button" className="link" disabled={loading} onClick={() => void refresh()}>Refresh streak</button>
    </div>
    {loading ? <p className="muted" role="status">Loading daily streak…</p> : null}
    {error ? <p className="error" role="alert">{error}{state ? " Showing the last loaded progress." : ""}</p> : null}
    {state ? <>
      <p className="streak-count"><strong>{state.current_streak}</strong> {state.current_streak === 1 ? "day" : "days"} in your current streak</p>
      <p className="muted">{state.streak_through ? <>Through <time dateTime={state.streak_through}>{dayLabel.format(asDate(state.streak_through))}</time>. </> : null}
        {today?.qualified ? "Today qualifies." : state.current_streak > 0 ? "Today can still qualify; your streak through yesterday stays intact." : "Save 60 active minutes in a day to begin a streak."}</p>
      <label id={progressId} className="streak-progress-label" htmlFor={`${progressId}-bar`}>
        Today · <time dateTime={state.today}>{dayLabel.format(asDate(state.today))}</time>: {savedTime(active)} of 60 min saved
      </label>
      <progress id={`${progressId}-bar`} aria-labelledby={progressId} value={Math.min(active, state.threshold_microseconds)} max={state.threshold_microseconds} />
      <ul className="streak-days" aria-label="Last seven days">
        {state.days.map((day) => <li key={day.date} className={day.qualified ? "streak-day qualified" : "streak-day"} aria-current={day.date === state.today ? "date" : undefined}>
          <time dateTime={day.date}><span>{weekdayLabel.format(asDate(day.date))}</span>{dayLabel.format(asDate(day.date))}</time>
          <span className="streak-day-result">{day.qualified ? "✓ Qualified" : day.date === state.today ? "In progress" : "Below goal"}</span>
          <span>{savedTime(day.active_microseconds)}</span>
        </li>)}
      </ul>
      <p className="muted">Dates use {state.timezone} from your local service. Changing the service timezone recalculates the days for saved work.</p>
    </> : null}
    <p className="muted">Reach 60 saved active minutes per day. Saved sessions count, including earlier sessions, early finishes and confirmed work from resolved interruptions. Running, paused and Needs review sessions count once saved. Pauses and uncertain gaps never count.</p>
  </section>;
}
