import { useEffect, useLayoutEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { resolveRoute } from "./routing";
import { publicRegistry } from "./registry";
import { ThemeToggle } from "./ThemeToggle";
import type { PublicPageContext, PublicPageDefinition } from "./types";

type State =
  | { status: "loading" }
  | { status: "not-found"; message?: string }
  | { status: "error"; message: string }
  | { status: "ready"; data: unknown };

export function PublicShell() {
  const route = useMemo(() => resolveRoute(window.location.pathname), []);
  const page: PublicPageDefinition | undefined = route
    ? publicRegistry[route.appId]?.[route.pageId]
    : undefined;
  const chrome = page?.chrome ?? "default";

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
        setState({ status: "ready", data });
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
      <Stage chrome={chrome}>
        <div className="pub-loader" aria-label="Carregando" />
      </Stage>
    );
  }

  if (state.status === "not-found" || state.status === "error") {
    const fallbackClass =
      chrome === "kiosk" ? "pub-fallback pub-fallback--fatal" : "pub-fallback";
    return (
      <Stage chrome={chrome}>
        <div className={fallbackClass}>
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

  return (
    <Stage chrome={chrome}>
      {state.status === "ready" && page ? page.render(state.data, route!) : null}
    </Stage>
  );
}

type StageProps = {
  children: ReactNode;
  chrome?: "default" | "kiosk" | "fullpage";
};

function Stage({ children, chrome = "default" }: StageProps) {
  useLayoutEffect(() => {
    if (chrome === "fullpage") {
      document.documentElement.classList.add("pub-fullpage");
      document.body.classList.add("pub-fullpage");
      return () => {
        document.documentElement.classList.remove("pub-fullpage");
        document.body.classList.remove("pub-fullpage");
      };
    }
    if (chrome !== "kiosk") return;
    document.documentElement.classList.add("pub-kiosk");
    document.body.classList.add("pub-kiosk");
    return () => {
      document.documentElement.classList.remove("pub-kiosk");
      document.body.classList.remove("pub-kiosk");
    };
  }, [chrome]);

  if (chrome === "kiosk") {
    return <div className="pub-kiosk-root">{children}</div>;
  }

  if (chrome === "fullpage") {
    return (
      <main className="pub-stage pub-stage--fullpage">
        <ThemeToggle />
        <div className="pub-logo pub-logo--compact">
          <img src="/p/logoMinhaDelpi.svg" alt="Minha DELPI" draggable={false} />
        </div>
        <div className="pub-content pub-content--fullpage">{children}</div>
      </main>
    );
  }

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
