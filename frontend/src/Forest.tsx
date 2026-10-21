import { useEffect, useRef, useState } from "react";
import { ApiError, getForest, type ForestTree } from "./api";
import { formatRemaining } from "./Countdown";
import { TreeArtwork } from "./Tree";

export function ForestCollection({ visible, lastSessionId }: { visible: boolean; lastSessionId: string | null }) {
  const [trees, setTrees] = useState<ForestTree[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const generation = useRef(0);

  useEffect(() => {
    if (!visible) return;
    const controller = new AbortController();
    const current = ++generation.current;
    setLoading(true);
    setError(null);
    void getForest(controller.signal).then((loaded) => {
      if (!controller.signal.aborted && current === generation.current) setTrees(loaded);
    }).catch((caught: unknown) => {
      if (!controller.signal.aborted && current === generation.current) setError(caught instanceof ApiError ? caught.message : "Could not load your forest. Try again.");
    }).finally(() => {
      if (!controller.signal.aborted && current === generation.current) setLoading(false);
    });
    return () => controller.abort();
  }, [visible, lastSessionId, refresh]);

  return <section className="forest-collection" aria-label="Forest collection" aria-busy={loading}>
    <div className="forest-heading">
      <h3>Your forest</h3>
      <button type="button" className="link" disabled={loading} onClick={() => setRefresh((value) => value + 1)}>Refresh forest</button>
    </div>
    <p className="muted">Pine is your free species. Trees begin with new countdowns started after this feature was installed; earlier sessions stay unchanged.</p>
    {loading ? <p className="muted" role="status">Loading forest…</p> : null}
    {error ? <p className="error" role="alert">{error} Use Refresh forest to try again.</p> : null}
    {trees?.length === 0 && !loading && !error ? <p className="forest-empty">Your forest is ready to grow. Finish a new countdown to save your first tree. Early finishes save an unfinished tree and your confirmed work.</p> : null}
    {trees && trees.length > 0 ? <ul className="forest-grid">
      {trees.map((tree) => <li key={tree.id} className="forest-tree" data-session-id={tree.session_id}>
        <TreeArtwork tree={tree} />
        <p className="tree-outcome">{tree.outcome === "mature" ? "Mature Pine" : "Unfinished Pine"}</p>
        <h4>{tree.task_title}</h4>
        <p className="muted">{[tree.project_name, tree.parent_title].filter(Boolean).join(" / ")}</p>
        <p>{formatRemaining(Math.floor(tree.active_seconds))} confirmed active time · {tree.duration_minutes} minute countdown</p>
        <p className="muted">Started <time dateTime={tree.started_at}>{new Date(tree.started_at).toLocaleString()}</time><br />Saved <time dateTime={tree.finished_at}>{new Date(tree.finished_at).toLocaleString()}</time></p>
      </li>)}
    </ul> : null}
  </section>;
}
