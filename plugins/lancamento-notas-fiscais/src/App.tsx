import { LnfPermissionsProvider } from "./application/LnfPermissionsContext";
import { configureHttpClient } from "./data/api/httpClient";
import { QueuePage } from "./ui/pages/QueuePage";
import { RequestDetailPage } from "./ui/pages/RequestDetailPage";
import { RequestFormPage } from "./ui/pages/RequestFormPage";
import { useCallback, useState } from "react";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

type View =
  | { name: "queue"; highlightId?: string }
  | { name: "create" }
  | { name: "detail"; requestId: string }
  | { name: "edit"; requestId: string };

export default function App({ getAccessToken }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const [view, setView] = useState<View>({ name: "queue" });

  const goQueue = useCallback((highlightId?: string) => {
    setView({ name: "queue", highlightId });
  }, []);

  return (
    <LnfPermissionsProvider>
      <div className="dashboard-lancamento-notas-fiscais lnf-page">
        {view.name === "queue" && (
          <QueuePage
            highlightId={view.highlightId}
            onCreate={() => setView({ name: "create" })}
            onOpen={(requestId) => setView({ name: "detail", requestId })}
          />
        )}
        {view.name === "create" && (
          <RequestFormPage
            mode="create"
            onCancel={() => goQueue()}
            onSuccess={(id) => goQueue(id)}
          />
        )}
        {view.name === "edit" && (
          <RequestFormPage
            mode="edit"
            requestId={view.requestId}
            onCancel={() => setView({ name: "detail", requestId: view.requestId })}
            onSuccess={(id) => setView({ name: "detail", requestId: id })}
          />
        )}
        {view.name === "detail" && (
          <RequestDetailPage
            requestId={view.requestId}
            onBack={() => goQueue()}
            onEdit={() => setView({ name: "edit", requestId: view.requestId })}
          />
        )}
      </div>
    </LnfPermissionsProvider>
  );
}
