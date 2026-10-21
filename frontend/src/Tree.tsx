import type { TreeProgress } from "./api";

/** Artwork and labels reflect saved backend progress, never browser timer ticks. */
export function TreeArtwork({ tree }: { tree: TreeProgress }) {
  return <svg className={`pine-art pine-${tree.stage}`} viewBox="0 0 160 180" role="img" aria-label={`Pine ${tree.stage}`}>
    <ellipse cx="80" cy="165" rx="53" ry="8" className="tree-ground" />
    {tree.stage === "seedling" ? <>
      <path d="M80 164V125" className="tree-trunk" />
      <path d="M80 143C53 145 48 126 50 119C68 117 79 127 80 143ZM80 133C80 112 97 105 111 110C111 126 97 136 80 133Z" className="tree-needles" />
    </> : tree.stage === "sapling" ? <>
      <path d="M80 164V101" className="tree-trunk" />
      <path d="M80 63L53 112H65L43 143H117L95 112H107Z" className="tree-needles" />
      <path d="M80 78L80 130" className="tree-highlight" />
    </> : <>
      <path d="M80 165V111" className="tree-trunk" />
      <path d="M80 20L49 78H61L36 112H49L22 147H138L111 112H124L99 78H111Z" className="tree-needles" />
      <path d="M80 38L62 72M80 77L53 106M80 115L50 139" className="tree-highlight" />
    </>}
  </svg>;
}

export function SessionTree({ tree, state }: { tree: TreeProgress; state: "running" | "paused" | "needs_review" | "finished" }) {
  const percent = Math.floor(Math.min(1, Math.max(0, tree.progress)) * 100);
  return <section className="session-tree" aria-label="Session tree">
    <TreeArtwork tree={tree} />
    <div>
      <h4>{tree.outcome === "mature" ? "Mature Pine" : tree.outcome === "unfinished" ? "Unfinished Pine" : `Pine · ${tree.stage}`}</h4>
      <p>{percent}% of your countdown confirmed</p>
      <progress max={1} value={tree.progress} aria-label="Confirmed tree growth" />
      <p className="muted">{tree.outcome === "mature" ? "Your completed tree is saved in your forest."
        : tree.outcome === "unfinished" ? "Your work and unfinished tree are saved in your forest."
        : state === "needs_review" ? "Growth is frozen at confirmed time. Uncertain time cannot grow this tree."
        : state === "paused" ? "Growth is preserved while paused."
        : "Grows with confirmed active time. A fully completed countdown plants a mature tree."}</p>
    </div>
  </section>;
}
