import { useMemo } from "react";
import { ConsoleShell, segmentFromPathname } from "./components/ConsoleShell";
import { CONSOLE_BASE } from "./constants/routes";
import { configureAuth } from "./lib/auth";
import { navigateConsole } from "./lib/consoleNavigation";
import { ExplorerPage } from "./pages/ExplorerPage";
import { HistoryPage } from "./pages/HistoryPage";
import { HomePage } from "./pages/HomePage";
import { SpecPage } from "./pages/SpecPage";
import { VerificacoesPage } from "./pages/VerificacoesPage";
import { DocumentacaoPage } from "./pages/DocumentacaoPage";
import "./index.css";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  basePath?: string;
  pathname?: string;
};

function normalizePathname(pathname?: string, basePath?: string): string {
  if (!pathname) return basePath ?? CONSOLE_BASE;
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

function renderPage(segment: string, onNavigate: (s: string) => void) {
  switch (segment) {
    case "documentacao":
      return <DocumentacaoPage onNavigate={onNavigate} />;
    case "verificacoes":
      return <VerificacoesPage onNavigate={onNavigate} />;
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

export default function App({
  getAccessToken,
  basePath,
  pathname: pathnameFromHost,
}: AppProps) {
  configureAuth(getAccessToken);

  const pathname = normalizePathname(
    pathnameFromHost ??
      (typeof window !== "undefined" ? window.location.pathname : undefined),
    basePath,
  );

  const segment = useMemo(
    () => segmentFromPathname(pathname, basePath),
    [pathname, basePath],
  );

  const onNavigate = (nextSegment: string) => navigateConsole(nextSegment, basePath);

  return (
    <ConsoleShell activeSegment={segment} onNavigate={onNavigate}>
      {renderPage(segment, onNavigate)}
    </ConsoleShell>
  );
}
