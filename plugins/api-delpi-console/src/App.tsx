import { useEffect, useState } from "react";
import { ConsoleShell, segmentFromPathname } from "./components/ConsoleShell";
import { CONSOLE_BASE } from "./constants/routes";
import { configureAuth } from "./lib/auth";
import { ExplorerPage } from "./pages/ExplorerPage";
import { HistoryPage } from "./pages/HistoryPage";
import { HomePage } from "./pages/HomePage";
import { SpecPage } from "./pages/SpecPage";
import { DocumentacaoPage } from "./pages/DocumentacaoPage";
import "./index.css";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  basePath?: string;
  pathname?: string;
};

function navigateTo(segment: string) {
  const next = segment ? `${CONSOLE_BASE}/${segment}` : CONSOLE_BASE;
  window.history.pushState({}, "", next);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

function renderPage(segment: string, onNavigate: (s: string) => void) {
  switch (segment) {
    case "documentacao":
      return <DocumentacaoPage onNavigate={onNavigate} />;
    case "explorer":
      return <ExplorerPage onNavigate={onNavigate} />;
    case "spec":
      return <SpecPage onNavigate={onNavigate} />;
    case "history":
      return <HistoryPage onNavigate={onNavigate} />;
    default:
      return <HomePage onNavigate={onNavigate} />;
  }
}

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureAuth(getAccessToken);

  const hostPathname =
    pathnameFromHost ??
    (typeof window !== "undefined" ? window.location.pathname : CONSOLE_BASE);

  const [segment, setSegment] = useState(() => segmentFromPathname(hostPathname));

  useEffect(() => {
    setSegment(segmentFromPathname(hostPathname));
  }, [hostPathname]);

  useEffect(() => {
    const onPop = () => setSegment(segmentFromPathname(window.location.pathname));
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  return (
    <ConsoleShell activeSegment={segment} onNavigate={navigateTo}>
      {renderPage(segment, navigateTo)}
    </ConsoleShell>
  );
}
