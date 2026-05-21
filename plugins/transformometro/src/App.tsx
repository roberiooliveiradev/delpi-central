import { useState } from "react";
import { DashboardPage } from "./ui/pages/DashboardPage";
import { HomePage } from "./ui/pages/HomePage";
import { ProcessoDetailPage } from "./ui/pages/ProcessoDetailPage";
import { ProcessosPage } from "./ui/pages/ProcessosPage";

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

  if (pathname === "/apps/transformometro/processos" || pathname?.endsWith("/processos")) {
    if (selectedProcessoId) {
      return (
        <ProcessoDetailPage
          getAccessToken={getAccessToken}
          processoId={selectedProcessoId}
          onBack={() => setSelectedProcessoId(null)}
        />
      );
    }
    return (
      <ProcessosPage
        getAccessToken={getAccessToken}
        onOpenProcesso={setSelectedProcessoId}
      />
    );
  }

  if (selectedProcessoId) {
    return (
      <ProcessoDetailPage
        getAccessToken={getAccessToken}
        processoId={selectedProcessoId}
        onBack={() => setSelectedProcessoId(null)}
      />
    );
  }

  return (
    <HomePage
      getAccessToken={getAccessToken}
      onGoDashboard={() => navigate("/apps/transformometro/dashboard")}
      onGoProcessos={() => navigate("/apps/transformometro/processos")}
    />
  );
}
