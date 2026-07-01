import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { resolveRoute } from "./routing";
import { publicRegistry } from "./registry";
import type { PublicPageContext, PublicPageDefinition } from "./types";

type State =
  | { status: "loading" }
  | { status: "not-found"; message?: string }
  | { status: "error"; message: string }
  | { status: "ready"; content: ReactNode };

export function PublicShell() {
  const route = useMemo(() => resolveRoute(window.location.pathname), []);
  const page: PublicPageDefinition | undefined = route
    ? publicRegistry[route.appId]?.[route.pageId]
    : undefined;

  const [state, setState] = useState<State>(() =>
    route && page ? { status: "loading" } : { status: "not-found" },
  );

  useEffect(() => {
    if (!route || !page) return;

    if (page.documentTitle) {
      document.title = page.documentTitle;
    }

    const ctx: PublicPageContext = route;
    let active = true;

    Promise.resolve(page.load(ctx))
      .then((data) => {
        if (!active) return;
        if (data === null || data === undefined) {
          setState({ status: "not-found", message: page.notFoundMessage });
          return;
        }
        setState({ status: "ready", content: page.render(data, ctx) });
      })
      .catch((err: unknown) => {
        if (!active) return;
        setState({
          status: "error",
          message: err instanceof Error ? err.message : "Erro inesperado.",
        });
      });

    return () => {
      active = false;
    };
  }, [route, page]);

  if (state.status === "loading") {
    return (
      <main className="pub-stage">
        <div className="pub-loader" aria-label="Carregando" />
      </main>
    );
  }

  if (state.status === "not-found" || state.status === "error") {
    return (
      <main className="pub-stage">
        <div className="pub-fallback">
          <div className="pub-brand">DELPI</div>
          <h1>{state.status === "not-found" ? "Página não encontrada" : "Ops!"}</h1>
          <p>
            {state.status === "not-found"
              ? state.message ?? "Este link não está mais disponível."
              : state.message}
          </p>
        </div>
      </main>
    );
  }

  return <main className="pub-stage">{state.content}</main>;
}
