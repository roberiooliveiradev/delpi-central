import { IssuancePermissionsProvider } from "./application/IssuancePermissionsContext";
import { configureHttpClient } from "./data/api/httpClient";
import { branchFromPathname, type BranchCode } from "./constants/branch";
import { QueuePage } from "./ui/pages/QueuePage";
import { RequestDetailPage } from "./ui/pages/RequestDetailPage";
import { IssuanceWizardPage } from "./ui/pages/IssuanceWizardPage";
import { useCallback, useState } from "react";
import * as api from "./data/api/invoiceIssuanceApi";
import type { IssuanceRequest } from "./domain/types";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

type View =
  | { name: "queue"; highlightId?: string }
  | { name: "create" }
  | { name: "detail"; requestId: string }
  | { name: "edit"; requestId: string; initial: IssuanceRequest };

function readRequestIdFromSearch(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const value = new URLSearchParams(window.location.search).get("requestId");
    const trimmed = value?.trim() ?? "";
    return trimmed || null;
  } catch {
    return null;
  }
}

export default function App({ getAccessToken, pathname }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const routeBranch = branchFromPathname(pathname);
  const [view, setView] = useState<View>(() => {
    const deepRequestId = readRequestIdFromSearch();
    return deepRequestId
      ? { name: "detail", requestId: deepRequestId }
      : { name: "queue" };
  });
  const [trackedBranch, setTrackedBranch] = useState(routeBranch);

  if (routeBranch !== trackedBranch) {
    setTrackedBranch(routeBranch);
    const deepRequestId = readRequestIdFromSearch();
    setView(
      deepRequestId
        ? { name: "detail", requestId: deepRequestId }
        : { name: "queue" },
    );
  }

  const goQueue = useCallback((highlightId?: string) => {
    setView({ name: "queue", highlightId });
  }, []);

  if (pathname && !routeBranch) {
    return (
      <div className="dashboard-invoice-issuance ii-page">
        <div className="ii-stack">
          <div className="ii-alert ii-error" role="alert" data-testid="invalid-route">
            <p>
              Rota inválida. Use /apps/invoice-issuance/filial-01 ou
              /apps/invoice-issuance/filial-02.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const branch: BranchCode = routeBranch ?? "01";

  return (
    <IssuancePermissionsProvider>
      <div className="dashboard-invoice-issuance ii-page">
        {view.name === "queue" && (
          <QueuePage
            branch={branch}
            highlightId={view.highlightId}
            onCreate={() => setView({ name: "create" })}
            onOpen={(requestId) => setView({ name: "detail", requestId })}
          />
        )}
        {view.name === "create" && (
          <IssuanceWizardPage
            mode="create"
            lockedBranch={branch}
            onCancel={() => goQueue()}
            onSuccess={(id) => goQueue(id)}
          />
        )}
        {view.name === "edit" && (
          <IssuanceWizardPage
            mode="edit"
            requestId={view.requestId}
            initial={view.initial}
            lockedBranch={branch}
            onCancel={() => setView({ name: "detail", requestId: view.requestId })}
            onSuccess={(id) => setView({ name: "detail", requestId: id })}
          />
        )}
        {view.name === "detail" && (
          <RequestDetailPage
            requestId={view.requestId}
            onBack={() => goQueue()}
            onEdit={() => {
              void api.getRequest(view.requestId).then((detail) => {
                setView({
                  name: "edit",
                  requestId: view.requestId,
                  initial: detail.request,
                });
              });
            }}
          />
        )}
      </div>
    </IssuancePermissionsProvider>
  );
}
