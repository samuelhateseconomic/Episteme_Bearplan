import type { TreeProgress, TreeSpecies } from "./api";

export const speciesName = (species: TreeSpecies) => ({ pine: "Pine", birch: "Birch", oak: "Oak", cherry: "Cherry" })[species];

/** Artwork and labels reflect saved backend progress, never browser timer ticks. */
export function TreeArtwork({ tree, decorative = false }: { tree: TreeProgress; decorative?: boolean }) {
  const broadleaf = tree.species !== "pine";
  return <svg className={`tree-art tree-${tree.species} tree-${tree.stage}`} viewBox="0 0 160 180" role="img" aria-hidden={decorative || undefined} aria-label={`${speciesName(tree.species)} ${tree.stage}`}>
    <ellipse cx="80" cy="165" rx="53" ry="8" className="tree-ground" />
    {tree.stage === "seedling" ? <>
      <path d="M80 164V125" className="tree-trunk" />
      <path d="M80 143C53 145 48 126 50 119C68 117 79 127 80 143ZM80 133C80 112 97 105 111 110C111 126 97 136 80 133Z" className="tree-needles" />
    </> : broadleaf ? <>
      <path d={tree.stage === "sapling" ? "M80 164V102M80 132L62 113M80 124L98 102" : "M80 165V72M80 127L49 95M80 111L109 76"} className="tree-trunk" />
      {tree.species === "birch" ? <>
        <ellipse cx="80" cy={tree.stage === "sapling" ? 92 : 66} rx={tree.stage === "sapling" ? 30 : 43} ry={tree.stage === "sapling" ? 39 : 53} className="tree-leaves" />
        <path d="M77 144H83M77 155H81" className="tree-bark" />
      </> : <>
        <path d={tree.stage === "sapling" ? "M47 110C33 88 52 69 67 76C72 51 106 53 108 79C133 81 132 113 111 118C93 133 58 131 47 110Z" : "M27 106C8 79 30 48 53 52C53 17 99 9 112 43C143 35 157 68 141 88C157 112 130 135 108 126C88 144 48 134 45 122C33 125 24 118 27 106Z"} className="tree-leaves" />
        {tree.species === "cherry" ? <g className="tree-blossoms">
          <circle cx="65" cy={tree.stage === "sapling" ? 94 : 56} r="5" /><circle cx="102" cy={tree.stage === "sapling" ? 101 : 93} r="5" /><circle cx="59" cy="111" r="4" />
        </g> : null}
      </>}
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
  const name = speciesName(tree.species);
  return <section className="session-tree" aria-label="Session tree">
    <TreeArtwork tree={tree} />
    <div>
      <h4>{tree.outcome === "mature" ? `Mature ${name}` : tree.outcome === "unfinished" ? `Unfinished ${name}` : `${name} · ${tree.stage}`}</h4>
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
