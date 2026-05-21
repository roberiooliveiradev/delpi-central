import { useState } from "react";
import { HomePage } from "./ui/pages/HomePage";
import { ProcessoDetailPage } from "./ui/pages/ProcessoDetailPage";
import { ProcessosPage } from "./ui/pages/ProcessosPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname }: AppProps) {
  const [selectedProcessoId, setSelectedProcessoId] = useState<string | null>(null);

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
      onGoProcessos={() => {
        window.history.pushState({}, "", "/apps/transformometro/processos");
        window.dispatchEvent(new PopStateEvent("popstate"));
      }}
    />
  );
}
