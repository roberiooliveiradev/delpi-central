import { LnfPermissionsProvider } from "./application/LnfPermissionsContext";
import { configureHttpClient } from "./data/api/httpClient";
import { branchFromPathname, type BranchCode } from "./constants/branch";
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

export default function App({ getAccessToken, pathname }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const routeBranch = branchFromPathname(pathname);
  const [view, setView] = useState<View>({ name: "queue" });
  const [trackedBranch, setTrackedBranch] = useState(routeBranch);

  if (routeBranch !== trackedBranch) {
    setTrackedBranch(routeBranch);
    setView({ name: "queue" });
  }

  const goQueue = useCallback((highlightId?: string) => {
    setView({ name: "queue", highlightId });
  }, []);

  if (pathname && !routeBranch) {
    return (
      <div className="dashboard-lancamento-notas-fiscais lnf-page">
        <div className="lnf-stack">
          <div className="lnf-alert lnf-error" role="alert" data-testid="invalid-route">
            <p>
              Rota inválida. Use /apps/lancamento-notas-fiscais/filial-01 ou
              /apps/lancamento-notas-fiscais/filial-02.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const branch: BranchCode = routeBranch ?? "01";

  return (
    <LnfPermissionsProvider>
      <div className="dashboard-lancamento-notas-fiscais lnf-page">
        {view.name === "queue" && (
          <QueuePage
            branch={branch}
            highlightId={view.highlightId}
            onCreate={() => setView({ name: "create" })}
            onOpen={(requestId) => setView({ name: "detail", requestId })}
          />
        )}
        {view.name === "create" && (
          <RequestFormPage
            mode="create"
            lockedBranch={branch}
            onCancel={() => goQueue()}
            onSuccess={(id) => goQueue(id)}
          />
        )}
        {view.name === "edit" && (
          <RequestFormPage
            mode="edit"
            requestId={view.requestId}
            lockedBranch={branch}
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
