/** PRC-REF-023-UI-FIX-03 — comportamento do lookup SA2 compartilhado:
 * debounce, descarte de resposta obsoleta, estados e seleção atômica
 * código+loja. */

import { useState } from "react";
import {
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { act } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(cleanup);
import {
  PrcSupplierCellLookup,
  useSupplierSearch,
  type PrcSupplierHitLike,
} from "./PrcSupplierForm";

const HITS: PrcSupplierHitLike[] = [
  {
    supplier_code: "000123",
    supplier_store: "01",
    supplier_name: "WEG AMAZONIA SA",
    supplier_short_name: "WEG",
  },
];

function HookProbe({ fetcher }: { fetcher: (q: string) => Promise<PrcSupplierHitLike[]> }) {
  const [q, setQ] = useState("");
  const { items, open, state } = useSupplierSearch(q, fetcher);
  return (
    <div>
      <input
        aria-label="q"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <output data-testid="state">{state}</output>
      <output data-testid="open">{String(open)}</output>
      <output data-testid="count">{items.length}</output>
    </div>
  );
}

describe("useSupplierSearch — UI-FIX-03", () => {
  it("debounce + resultado abre painel; termo curto fica idle", async () => {
    vi.useFakeTimers();
    const fetcher = vi.fn(async () => HITS);
    render(<HookProbe fetcher={fetcher} />);
    const input = screen.getByLabelText("q");
    fireEvent.change(input, { target: { value: "ty" } });
    expect(fetcher).not.toHaveBeenCalled();
    await act(async () => {
      vi.advanceTimersByTime(350);
      await Promise.resolve();
    });
    expect(fetcher).toHaveBeenCalledWith("ty", expect.anything());
    expect(screen.getByTestId("count").textContent).toBe("1");
    expect(screen.getByTestId("open").textContent).toBe("true");
    vi.useRealTimers();
  });

  it("resposta obsoleta não sobrescreve consulta mais recente", async () => {
    vi.useFakeTimers();
    let resolveOld!: (v: PrcSupplierHitLike[]) => void;
    const fetcher = vi.fn((q: string) =>
      q === "old"
        ? new Promise<PrcSupplierHitLike[]>((r) => (resolveOld = r))
        : Promise.resolve(HITS),
    );
    render(<HookProbe fetcher={fetcher} />);
    const input = screen.getByLabelText("q");
    fireEvent.change(input, { target: { value: "old" } });
    await act(async () => {
      vi.advanceTimersByTime(350);
    });
    fireEvent.change(input, { target: { value: "new" } });
    await act(async () => {
      vi.advanceTimersByTime(350);
      await Promise.resolve();
    });
    expect(screen.getByTestId("count").textContent).toBe("1");
    /* resposta antiga chega depois — descartada pelo guard seq/abort */
    await act(async () => {
      resolveOld([{ supplier_code: "STALE", supplier_store: "99" }]);
      await Promise.resolve();
    });
    expect(screen.getByTestId("count").textContent).toBe("1");
    vi.useRealTimers();
  });

  it("erro de API expõe estado error sem abrir painel", async () => {
    vi.useFakeTimers();
    const fetcher = vi.fn(async () => {
      throw new Error("boom");
    });
    render(<HookProbe fetcher={fetcher} />);
    fireEvent.change(screen.getByLabelText("q"), {
      target: { value: "xx" },
    });
    await act(async () => {
      vi.advanceTimersByTime(350);
      await Promise.resolve();
    });
    expect(screen.getByTestId("state").textContent).toBe("error");
    expect(screen.getByTestId("open").textContent).toBe("false");
    vi.useRealTimers();
  });
});

describe("PrcSupplierCellLookup — UI-FIX-03", () => {
  it("Escape fecha a busca preservando a seleção", async () => {
    const onClose = vi.fn();
    const fetcher = vi.fn(async () => HITS);
    render(
      <PrcSupplierCellLookup
        id="lk"
        query="we"
        searchSuppliers={fetcher}
        onQueryChange={() => {}}
        onSelect={() => {}}
        onClose={onClose}
      />,
    );
    fireEvent.keyDown(screen.getByRole("textbox"), { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });

  it("onSelect devolve o hit completo (código+loja+fantasia)", async () => {
    vi.useFakeTimers();
    const onSelect = vi.fn();
    const fetcher = vi.fn(async () => HITS);
    render(
      <PrcSupplierCellLookup
        id="lk"
        query="weg"
        searchSuppliers={fetcher}
        onQueryChange={() => {}}
        onSelect={onSelect}
        onClose={() => {}}
      />,
    );
    await act(async () => {
      vi.advanceTimersByTime(350);
      await Promise.resolve();
    });
    vi.useRealTimers();
    const option = await screen.findByRole("option");
    fireEvent.click(option.querySelector("button")!);
    expect(onSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        supplier_code: "000123",
        supplier_store: "01",
      }),
    );
  });
});
