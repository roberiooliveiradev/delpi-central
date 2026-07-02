import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { resolveRoute } from "./routing";
import { publicRegistry } from "./registry";
import { ThemeToggle } from "./ThemeToggle";
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
      <Stage>
        <div className="pub-loader" aria-label="Carregando" />
      </Stage>
    );
  }

  if (state.status === "not-found" || state.status === "error") {
    return (
      <Stage>
        <div className="pub-fallback">
          <h1>{state.status === "not-found" ? "Página não encontrada" : "Ops!"}</h1>
          <p>
            {state.status === "not-found"
              ? state.message ?? "Este link não está mais disponível."
              : state.message}
          </p>
        </div>
      </Stage>
    );
  }

  return <Stage>{state.content}</Stage>;
}

/** Palco transversal da marca: logo Minha DELPI no topo + conteúdo centralizado. */
function Stage({ children }: { children: ReactNode }) {
  return (
    <main className="pub-stage">
      <ThemeToggle />
      <div className="pub-logo">
        <img src="/p/logoMinhaDelpi.svg" alt="Minha DELPI" draggable={false} />
      </div>
      <div className="pub-content">{children}</div>
    </main>
  );
}
