import { useCallback, useEffect, useState } from "react";

export type CockpitView =
  | { kind: "queue" }
  | { kind: "operation"; productionOrder: string; operationCode: string }
  | { kind: "performance" };

const QUEUE_VIEW: CockpitView = { kind: "queue" };

/**
 * Estado de tela do cockpit espelhado na query string.
 *
 * `resolveRoute` só aceita `/p/{app}/{page}/{token}`, então a navegação interna
 * vive em `?view=`/`?op=`/`?operation=` — recarregar o tablet volta à mesma tela.
 */
export function useCockpitView(): {
  view: CockpitView;
  openQueue: () => void;
  openOperation: (productionOrder: string, operationCode: string) => void;
  openPerformance: () => void;
} {
  const [view, setView] = useState<CockpitView>(() => readViewFromLocation());

  const apply = useCallback((next: CockpitView) => {
    setView(next);
    writeViewToLocation(next);
  }, []);

  useEffect(() => {
    // Botão «voltar» do tablet: o histórico é do shell, mas a query é nossa.
    const onPopState = () => setView(readViewFromLocation());
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  return {
    view,
    openQueue: useCallback(() => apply(QUEUE_VIEW), [apply]),
    openOperation: useCallback(
      (productionOrder: string, operationCode: string) =>
        apply({ kind: "operation", productionOrder, operationCode }),
      [apply],
    ),
    openPerformance: useCallback(() => apply({ kind: "performance" }), [apply]),
  };
}

export function readViewFromLocation(search = window.location.search): CockpitView {
  const params = new URLSearchParams(search);
  const kind = params.get("view");
  if (kind === "performance") return { kind: "performance" };
  if (kind === "operation") {
    const productionOrder = (params.get("op") || "").trim();
    const operationCode = (params.get("operation") || "").trim();
    if (productionOrder && operationCode) {
      return { kind: "operation", productionOrder, operationCode };
    }
  }
  return QUEUE_VIEW;
}

function writeViewToLocation(view: CockpitView): void {
  const params = new URLSearchParams(window.location.search);
  params.delete("view");
  params.delete("op");
  params.delete("operation");

  if (view.kind === "performance") {
    params.set("view", "performance");
  } else if (view.kind === "operation") {
    params.set("view", "operation");
    params.set("op", view.productionOrder);
    params.set("operation", view.operationCode);
  }

  const query = params.toString();
  const next = `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`;
  window.history.replaceState(window.history.state, "", next);
}
