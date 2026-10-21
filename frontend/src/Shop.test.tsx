import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, vi } from "vitest";
import { TreeShop, useShop } from "./Shop";
import type { ShopState } from "./api";

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
const state = (over: Partial<ShopState> = {}): ShopState => ({
  balance: 60, coins_per_minute: 1,
  species: [
    { id: "pine", name: "Pine", price: 0, owned: true },
    { id: "birch", name: "Birch", price: 30, owned: false },
    { id: "oak", name: "Oak", price: 60, owned: false },
    { id: "cherry", name: "Cherry", price: 120, owned: false },
  ], recent_entries: [], ...over,
});
function Harness({ visible = true, lastSessionId = null }: { visible?: boolean; lastSessionId?: string | null }) {
  return <TreeShop shop={useShop(visible, lastSessionId)} />;
}

beforeEach(() => sessionStorage.clear());
afterEach(() => sessionStorage.clear());

test("wallet uses configured prices and rate, owned species stay available and insufficient spending is disabled", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(json(state({ coins_per_minute: 3 })));
  render(<Harness />);
  await waitFor(() => expect(screen.getByText("Your coins:")).toHaveTextContent("60"));
  expect(screen.getByText(/Earn 3 coins per whole confirmed active minute/)).toBeVisible();
  expect(screen.getByRole("button", { name: "Buy Birch for 30 coins" })).toBeEnabled();
  expect(screen.getByRole("button", { name: "Buy Oak for 60 coins" })).toBeEnabled();
  expect(screen.getByRole("button", { name: "Buy Cherry for 120 coins" })).toBeDisabled();
  expect(screen.queryByRole("button", { name: /Buy Pine/ })).not.toBeInTheDocument();
  expect(screen.getByText("Free · Owned")).toBeVisible();
  for (const species of ["Pine", "Birch", "Oak", "Cherry"]) expect(screen.getByRole("heading", { name: species })).toBeVisible();
});

test("a deliberate purchase sends its displayed price and saves ownership with an authoritative wallet refresh", async () => {
  let current = state();
  const sent: Record<string, unknown>[] = [];
  vi.spyOn(globalThis, "fetch").mockImplementation(async (_input, init) => {
    if (init?.method === "POST") {
      sent.push(JSON.parse(String(init.body)) as Record<string, unknown>);
      current = { ...current, balance: 30, species: current.species.map((item) => item.id === "birch" ? { ...item, owned: true } : item) };
      return json({ ...sent[0], price: 30, balance: 30 });
    }
    return json(current);
  });
  const user = userEvent.setup();
  render(<Harness />);
  const buy = await screen.findByRole("button", { name: "Buy Birch for 30 coins" });
  buy.focus();
  await user.keyboard("{Enter}");
  expect(await screen.findByText(/Birch is owned and ready/)).toBeVisible();
  expect(screen.getByText("Your coins:")).toHaveTextContent("30");
  expect(screen.queryByRole("button", { name: /Buy Birch/ })).not.toBeInTheDocument();
  expect(sent).toEqual([{ species: "birch", expected_price: 30, operation_id: expect.any(String) }]);
  expect(sessionStorage.getItem("bearplans.shop.pending")).toBeNull();
});

test("a lost purchase response survives reload and retries the identical request without replacing the wallet with a stale replay balance", async () => {
  let current = state();
  let readsUnavailable = false;
  const attempts: Record<string, unknown>[] = [];
  vi.spyOn(globalThis, "fetch").mockImplementation(async (_input, init) => {
    if (init?.method === "POST") {
      attempts.push(JSON.parse(String(init.body)) as Record<string, unknown>);
      if (attempts.length === 1) {
        current = { ...current, balance: 30, species: current.species.map((item) => item.id === "birch" ? { ...item, owned: true } : item) };
        readsUnavailable = true;
        throw new TypeError("Lost response after commit");
      }
      // Another saved action has since changed the wallet. The replay receipt is older.
      current = { ...current, balance: 12 };
      readsUnavailable = false;
      return json({ operation_id: attempts[0].operation_id, species: "birch", price: 30, balance: 30 });
    }
    if (readsUnavailable) throw new TypeError("Disconnected");
    return json(current);
  });
  const user = userEvent.setup();
  const first = render(<Harness />);
  await user.click(await screen.findByRole("button", { name: "Buy Birch for 30 coins" }));
  expect(await screen.findByText(/Your purchase request is kept/)).toBeVisible();
  expect(sessionStorage.getItem("bearplans.shop.pending")).toContain(String(attempts[0].operation_id));
  expect(screen.getByRole("button", { name: "Buy Oak for 60 coins" })).toBeDisabled();
  first.unmount();
  render(<Harness />);
  const retry = await screen.findByRole("button", { name: "Retry Birch purchase for 30 coins" });
  await waitFor(() => expect(retry).toBeEnabled());
  await user.click(retry);
  await waitFor(() => expect(screen.getByText("Your coins:")).toHaveTextContent("12"));
  expect(attempts).toHaveLength(2);
  expect(attempts[1]).toEqual(attempts[0]);
  expect(screen.queryByRole("button", { name: /Retry Birch/ })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /Buy Birch/ })).not.toBeInTheDocument();
  expect(sessionStorage.getItem("bearplans.shop.pending")).toBeNull();
});

test("an authoritative owned result acknowledges a lost response without a second debit", async () => {
  let current = state();
  let purchases = 0;
  vi.spyOn(globalThis, "fetch").mockImplementation(async (_input, init) => {
    if (init?.method === "POST") {
      purchases += 1;
      current = { ...current, balance: 30, species: current.species.map((item) => item.id === "birch" ? { ...item, owned: true } : item) };
      throw new TypeError("Lost response");
    }
    return json(current);
  });
  const user = userEvent.setup();
  render(<Harness />);
  await user.click(await screen.findByRole("button", { name: /Buy Birch/ }));
  expect(await screen.findByText(/Birch is owned and ready/)).toBeVisible();
  expect(screen.getByText("Your coins:")).toHaveTextContent("30");
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  expect(purchases).toBe(1);
  expect(sessionStorage.getItem("bearplans.shop.pending")).toBeNull();
});

test("a price conflict retains the catalog, explains the error, and uses a fresh request for the new displayed price", async () => {
  let current = state();
  const attempts: Record<string, unknown>[] = [];
  vi.spyOn(globalThis, "fetch").mockImplementation(async (_input, init) => {
    if (init?.method === "POST") {
      attempts.push(JSON.parse(String(init.body)) as Record<string, unknown>);
      if (attempts.length === 1) {
        current = { ...current, species: current.species.map((item) => item.id === "birch" ? { ...item, price: 31 } : item) };
        return json({ error: { message: "The price changed. Review the shop before buying." } }, 409);
      }
      current = { ...current, balance: 29, species: current.species.map((item) => item.id === "birch" ? { ...item, owned: true } : item) };
      return json({ operation_id: attempts[1].operation_id, species: "birch", price: 31, balance: 29 });
    }
    return json(current);
  });
  const user = userEvent.setup();
  render(<Harness />);
  await user.click(await screen.findByRole("button", { name: "Buy Birch for 30 coins" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("The price changed");
  await user.click(await screen.findByRole("button", { name: "Buy Birch for 31 coins" }));
  expect(await screen.findByText(/Birch is owned and ready/)).toBeVisible();
  expect(attempts[0].expected_price).toBe(30);
  expect(attempts[1].expected_price).toBe(31);
  expect(attempts[0].operation_id).not.toBe(attempts[1].operation_id);
});

test("all purchase controls stay disabled while saving and become retryable after a failed save", async () => {
  let rejectPurchase!: (error: unknown) => void;
  vi.spyOn(globalThis, "fetch").mockImplementation(async (_input, init) => init?.method === "POST"
    ? new Promise<Response>((_resolve, reject) => { rejectPurchase = reject; }) : json(state()));
  const user = userEvent.setup();
  render(<Harness />);
  await user.click(await screen.findByRole("button", { name: /Buy Birch/ }));
  const shop = screen.getByRole("region", { name: "Tree shop" });
  expect(shop).toHaveAttribute("aria-busy", "true");
  for (const button of within(shop).getAllByRole("button")) expect(button).toBeDisabled();
  await act(async () => rejectPurchase(new TypeError("Disconnected")));
  expect(await screen.findByRole("alert")).toHaveTextContent("Your purchase request is kept");
  expect(screen.getByRole("button", { name: "Retry Birch purchase for 30 coins" })).toBeEnabled();
  expect(screen.getByRole("button", { name: /Buy Oak/ })).toBeDisabled();
});

test("failed refresh keeps the last wallet visible, blocks stale spending, and supports retry", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(state()))
    .mockRejectedValueOnce(new TypeError("Disconnected"))
    .mockResolvedValue(json(state({ balance: 5 })));
  const user = userEvent.setup();
  render(<Harness />);
  await screen.findByRole("button", { name: /Buy Birch/ });
  await user.click(screen.getByRole("button", { name: "Refresh shop" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Refresh shop to check your current coins");
  expect(screen.getByText("Your coins:")).toHaveTextContent("60");
  expect(screen.getByRole("button", { name: /Buy Birch/ })).toBeDisabled();
  await user.click(screen.getByRole("button", { name: "Refresh shop" }));
  await waitFor(() => expect(screen.getByText("Your coins:")).toHaveTextContent("5"));
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  expect(fetcher).toHaveBeenCalledTimes(3);
});

test("focus, tab visibility, Track visibility, and a saved session refresh the wallet without buying", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockImplementation(async () => json(state()));
  const { rerender } = render(<Harness visible={false} />);
  expect(fetcher).not.toHaveBeenCalled();
  rerender(<Harness />);
  await screen.findByRole("button", { name: /Buy Birch/ });
  fireEvent(window, new Event("focus"));
  await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));
  fireEvent(document, new Event("visibilitychange"));
  await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(3));
  rerender(<Harness lastSessionId="newly-saved-session" />);
  await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(4));
  expect(fetcher.mock.calls.every(([, init]) => !init?.method)).toBe(true);
});

test("negative balances disable spending while owned species remain available", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(json(state({ balance: -5 })));
  render(<Harness />);
  await waitFor(() => expect(screen.getByText("Your coins:")).toHaveTextContent("-5"));
  for (const button of screen.getAllByRole("button", { name: /^Buy / })) expect(button).toBeDisabled();
  expect(screen.getByText("35 more coins needed")).toBeVisible();
  expect(screen.getByText("Ready to grow")).toBeVisible();
});

test("a superseded wallet read cannot overwrite a newer balance and ownership", async () => {
  let resolveOld!: (response: Response) => void;
  const current = state({ balance: 5 });
  current.species[1] = { ...current.species[1], owned: true };
  const fetcher = vi.spyOn(globalThis, "fetch").mockImplementationOnce(() => new Promise<Response>((resolve) => { resolveOld = resolve; }))
    .mockResolvedValue(json(current));
  render(<Harness />);
  fireEvent(window, new Event("focus"));
  await waitFor(() => expect(screen.getByText("Your coins:")).toHaveTextContent("5"));
  await act(async () => resolveOld(json(state())));
  expect(screen.getByText("Your coins:")).toHaveTextContent("5");
  expect(screen.queryByRole("button", { name: /Buy Birch/ })).not.toBeInTheDocument();
  expect(fetcher).toHaveBeenCalledTimes(2);
});

test("purchase is not sent if its retry request cannot be persisted before sending", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(json(state()));
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("Storage unavailable"); });
  const user = userEvent.setup();
  render(<Harness />);
  await user.click(await screen.findByRole("button", { name: /Buy Birch/ }));
  expect(await screen.findByRole("alert")).toHaveTextContent("No purchase was sent");
  expect(fetcher.mock.calls.every(([, init]) => !init?.method)).toBe(true);
});
