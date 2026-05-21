import { useState } from "react";
import { DashboardPage } from "./ui/pages/DashboardPage";
import { HomePage } from "./ui/pages/HomePage";
import { ProcessoDetailPage } from "./ui/pages/ProcessoDetailPage";
import { ImportPage } from "./ui/pages/ImportPage";
import { ProcessosPage } from "./ui/pages/ProcessosPage";
import { RecursosPage } from "./ui/pages/RecursosPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

function navigate(path: string) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export default function App({ getAccessToken, pathname }: AppProps) {
  const [selectedProcessoId, setSelectedProcessoId] = useState<string | null>(null);

  if (pathname === "/apps/transformometro/dashboard" || pathname?.endsWith("/dashboard")) {
    return (
      <DashboardPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        onNavigate={navigate}
      />
    );
  }

  if (pathname === "/apps/transformometro/import" || pathname?.endsWith("/import")) {
    return (
      <ImportPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        onNavigate={navigate}
      />
    );
  }

  if (pathname === "/apps/transformometro/recursos" || pathname?.endsWith("/recursos")) {
    return (
      <RecursosPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        onNavigate={navigate}
      />
    );
  }

  if (pathname === "/apps/transformometro/processos" || pathname?.endsWith("/processos")) {
    if (selectedProcessoId) {
      return (
        <ProcessoDetailPage
          getAccessToken={getAccessToken}
          processoId={selectedProcessoId}
          pathname={pathname}
          onNavigate={navigate}
          onBack={() => setSelectedProcessoId(null)}
        />
      );
    }
    return (
      <ProcessosPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        onNavigate={navigate}
        onOpenProcesso={setSelectedProcessoId}
      />
    );
  }

  if (selectedProcessoId) {
    return (
      <ProcessoDetailPage
        getAccessToken={getAccessToken}
        processoId={selectedProcessoId}
        pathname={pathname}
        onNavigate={navigate}
        onBack={() => setSelectedProcessoId(null)}
      />
    );
  }

  return (
    <HomePage
      getAccessToken={getAccessToken}
      pathname={pathname}
      onNavigate={navigate}
    />
  );
}
