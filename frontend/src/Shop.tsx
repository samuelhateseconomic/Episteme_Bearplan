import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, getShop, purchaseSpecies, type ShopSpecies, type ShopState, type TreeSpecies } from "./api";
import { speciesName, TreeArtwork } from "./Tree";

const PENDING_KEY = "bearplans.shop.pending";
interface PendingPurchase { species: TreeSpecies; expectedPrice: number; operationId: string }
const errorMessage = (error: unknown) => error instanceof ApiError ? error.message : "Could not save your purchase. Please try again.";

function readPending(): PendingPurchase | null {
  try {
    const value: unknown = JSON.parse(sessionStorage.getItem(PENDING_KEY) ?? "null");
    if (value && typeof value === "object" && "species" in value && ["birch", "oak", "cherry"].includes(String(value.species))
      && "expectedPrice" in value && typeof value.expectedPrice === "number" && Number.isInteger(value.expectedPrice) && value.expectedPrice >= 0
      && "operationId" in value && typeof value.operationId === "string") return value as PendingPurchase;
  } catch { /* Report an unavailable store before sending a purchase. */ }
  return null;
}

/** Wallet reads are authoritative; purchase receipts may describe an older balance. */
export function useShop(visible: boolean, lastSessionId: string | null) {
  const [state, setState] = useState<ShopState | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [pending, setPending] = useState<PendingPurchase | null>(readPending);
  const pendingRef = useRef(pending);
  const busyRef = useRef(false);
  const request = useRef<AbortController | null>(null);
  const generation = useRef(0);

  const clearPending = useCallback(() => {
    pendingRef.current = null;
    setPending(null);
    try { sessionStorage.removeItem(PENDING_KEY); } catch { /* A saved replay is still safe. */ }
  }, []);

  const refresh = useCallback(async () => {
    if (busyRef.current) return;
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    const current = ++generation.current;
    setLoading(true);
    try {
      const loaded = await getShop(controller.signal);
      if (controller.signal.aborted || current !== generation.current) return;
      setState(loaded);
      setLoadError(null);
      const attempted = pendingRef.current;
      if (attempted && loaded.species.some((item) => item.id === attempted.species && item.owned)) {
        clearPending();
        setActionError(null);
        setNotice(`${speciesName(attempted.species)} is owned and ready for your next countdown.`);
      }
    } catch (caught) {
      if (!controller.signal.aborted && current === generation.current) setLoadError(caught instanceof ApiError && caught.status === 404
        ? "The tree shop needs the updated local service. Restart BearPlans, then use Refresh shop. Pine countdowns are still available."
        : `${errorMessage(caught)} Use Refresh shop to check your current coins and species.`);
    } finally {
      if (!controller.signal.aborted && current === generation.current) setLoading(false);
    }
  }, [clearPending]);

  useEffect(() => {
    if (!visible) return;
    void refresh();
    const recheck = () => { if (document.visibilityState !== "hidden") void refresh(); };
    window.addEventListener("focus", recheck);
    document.addEventListener("visibilitychange", recheck);
    return () => {
      window.removeEventListener("focus", recheck);
      document.removeEventListener("visibilitychange", recheck);
      request.current?.abort();
      generation.current += 1;
    };
  }, [visible, lastSessionId, refresh]);

  async function buy(species: ShopSpecies | PendingPurchase) {
    if (busyRef.current) return;
    let attempt = pendingRef.current;
    if (!attempt) {
      if (!("price" in species)) return;
      attempt = { species: species.id, expectedPrice: species.price, operationId: crypto.randomUUID() };
      try { sessionStorage.setItem(PENDING_KEY, JSON.stringify(attempt)); }
      catch {
        setActionError("Your browser could not keep the purchase request. Allow browser storage and try again. No purchase was sent.");
        return;
      }
      pendingRef.current = attempt;
      setPending(attempt);
    }
    busyRef.current = true;
    setBusy(true);
    setActionError(null);
    setNotice(null);
    request.current?.abort();
    generation.current += 1;
    setLoading(false);
    try {
      await purchaseSpecies(attempt.species, attempt.expectedPrice, attempt.operationId);
      clearPending();
      setNotice(`${speciesName(attempt.species)} is owned and ready for your next countdown.`);
    } catch (caught) {
      const rejected = caught instanceof ApiError && caught.status !== undefined && caught.status >= 400 && caught.status < 500;
      if (rejected) clearPending();
      setActionError(`${errorMessage(caught)} ${rejected ? "Review the refreshed shop before trying again." : "Your purchase request is kept. Refresh shop to check, or retry this purchase safely."}`);
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
    await refresh();
  }

  return { state, loading, busy, loadError, actionError, notice, pending, refresh, buy };
}

export type Shop = ReturnType<typeof useShop>;

export function TreeShop({ shop }: { shop: Shop }) {
  return <section className="tree-shop" aria-labelledby="shop-heading" aria-busy={shop.busy || shop.loading}>
    <div className="forest-heading">
      <h3 id="shop-heading">Tree shop</h3>
      <button type="button" className="link" disabled={shop.busy || shop.loading} onClick={() => void shop.refresh()}>Refresh shop</button>
    </div>
    <p className="coin-balance">Your coins: <strong>{shop.state ? shop.state.balance.toLocaleString() : "—"}</strong></p>
    {shop.state ? <p className="muted">Earn {shop.state.coins_per_minute} {shop.state.coins_per_minute === 1 ? "coin" : "coins"} per whole confirmed active minute when a new countdown is saved. Paused and uncertain time earn no coins. Earlier sessions stay unchanged.</p> : null}
    {shop.loading ? <p role="status" className="muted">Loading coins and species…</p> : null}
    {shop.loadError ? <p className="error" role="alert">{shop.loadError}</p> : null}
    {shop.actionError ? <p className="error" role="alert">{shop.actionError}</p> : null}
    {shop.notice ? <p role="status">{shop.notice}</p> : null}
    {shop.pending ? <div className="purchase-retry">
      <p>Check the saved result of your {speciesName(shop.pending.species)} purchase before buying another species.</p>
      <button type="button" className="secondary" disabled={shop.busy || shop.loading} onClick={() => void shop.buy(shop.pending!)}>
        {shop.busy ? "Checking purchase…" : `Retry ${speciesName(shop.pending.species)} purchase for ${shop.pending.expectedPrice} coins`}
      </button>
    </div> : null}
    {shop.state ? <ul className="shop-grid">
      {shop.state.species.map((item) => <li key={item.id} className="shop-species">
        <TreeArtwork decorative tree={{ id: `shop-${item.id}`, species: item.id, stage: "mature", progress: 1, outcome: "mature" }} />
        <h4>{item.name}</h4>
        <p>{item.price === 0 ? "Free" : `${item.price} coins`}{item.owned ? " · Owned" : ""}</p>
        {item.owned ? <p className="muted">Ready to grow</p> : <>
          <button type="button" disabled={shop.busy || shop.loading || Boolean(shop.loadError) || Boolean(shop.pending) || shop.state!.balance < item.price || shop.state!.balance < 0}
            onClick={() => void shop.buy(item)}>Buy {item.name} for {item.price} coins</button>
          {shop.state!.balance < item.price ? <p className="muted">{item.price - shop.state!.balance} more coins needed</p> : null}
        </>}
      </li>)}
    </ul> : null}
    {shop.state && shop.state.recent_entries.length > 0 ? <details className="coin-history">
      <summary>Recent coin activity</summary>
      <ul>{shop.state.recent_entries.map((entry) => <li key={entry.id}>
        <span>{entry.kind === "purchase" && entry.species ? `${speciesName(entry.species)} purchase` : entry.kind === "session_adjustment" ? "Session correction" : "Session saved"}</span>
        <strong>{entry.amount > 0 ? "+" : ""}{entry.amount} coins</strong>
        <time dateTime={entry.created_at}>{new Date(entry.created_at).toLocaleString()}</time>
      </li>)}</ul>
    </details> : null}
    <p className="muted">Species are cosmetic and stay yours. Choose an owned species before starting your next countdown.</p>
  </section>;
}
