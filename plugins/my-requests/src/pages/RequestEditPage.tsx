import { ActionButton } from "@delpi/plugin-ui/index";
import { useEffect, useState } from "react";

import { useMyRequestsFloatingNotice } from "../app/MyRequestsFloatingNoticeProvider";
import { getRequest, listRequestTypes } from "../api/requestsApi";
import { AppShell } from "../components/AppShell";
import { InvoiceIssuanceWizard } from "../features/invoice-issuance/ui/InvoiceIssuanceWizard";
import { SchemaFormPage } from "../features/raw-material-creation/SchemaFormPage";
import {
  myRequestsPath,
  navigateMyRequestsPath,
} from "../hooks/myRequestsNavigation";
import { canCreateAnyRequest } from "../security/requestsAccess";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import type { RequestDetail, RequestTypeSummary } from "../types/requests";
import {
  MyRequestsLoadingState,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
} from "../ui/mrUi";
import { GenericCreateForm } from "./GenericCreateForm";
import {
  isInvoiceIssuanceSpecialized,
  resolveOpenMode,
} from "./resolveOpenMode";

type RequestEditPageProps = {
  requestId: string;
};

export function RequestEditPage({ requestId }: RequestEditPageProps) {
  const access = useRequestsPermissions();
  const { notifyError } = useMyRequestsFloatingNotice();
  const [request, setRequest] = useState<RequestDetail | null>(null);
  const [requestType, setRequestType] = useState<RequestTypeSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const ac = new AbortController();
    setLoading(true);
    Promise.all([
      getRequest(requestId, { signal: ac.signal }),
      listRequestTypes({ signal: ac.signal }),
    ])
      .then(([detail, types]) => {
        if (!(detail.allowed_actions || []).includes("edit")) {
          setError("Esta solicitação não pode ser editada no momento.");
          setRequest(detail);
          return;
        }
        const match = types.find((row) => row.code === detail.type_code) || null;
        if (!match) {
          setError("Tipo de solicitação não encontrado para edição.");
          setRequest(detail);
          return;
        }
        setRequest(detail);
        setRequestType(match);
        setError(null);
      })
      .catch((err: Error) => {
        if (err.name !== "AbortError") {
          setError(err.message);
          notifyError(err.message);
        }
      })
      .finally(() => {
        if (!ac.signal.aborted) setLoading(false);
      });
    return () => ac.abort();
  }, [notifyError, requestId]);

  function goDetail() {
    navigateMyRequestsPath(myRequestsPath({ requestId }));
  }

  if (loading) {
    return (
      <AppShell title="Corrigir solicitação" canCreate={canCreateAnyRequest(access)}>
        <MyRequestsLoadingState />
      </AppShell>
    );
  }

  if (error || !request || !requestType) {
    return (
      <AppShell title="Corrigir solicitação" canCreate={canCreateAnyRequest(access)}>
        <MyRequestsSectionCard title="Edição indisponível">
          <MyRequestsStateBanner variant="error">
            {error || "Não foi possível abrir a edição."}
          </MyRequestsStateBanner>
          <ActionButton type="button" variant="ghost" onClick={goDetail}>
            Voltar ao detalhe
          </ActionButton>
        </MyRequestsSectionCard>
      </AppShell>
    );
  }

  if (isInvoiceIssuanceSpecialized(requestType)) {
    return (
      <InvoiceIssuanceWizard
        requestType={requestType}
        mode="edit"
        requestId={request.id}
        initialPayload={request.payload}
        initialVersion={request.version}
        lockedBranch={request.branch_code || undefined}
        onCancel={goDetail}
      />
    );
  }

  const openMode = resolveOpenMode(requestType);
  if (openMode === "schema_driven") {
    return (
      <SchemaFormPage
        requestType={requestType}
        mode="edit"
        requestId={request.id}
        initialPayload={request.payload}
        initialVersion={request.version}
        lockedBranch={request.branch_code || undefined}
        onCancel={goDetail}
      />
    );
  }

  return (
    <GenericCreateForm
      requestType={requestType}
      mode="edit"
      requestId={request.id}
      initialPayload={request.payload}
      initialVersion={request.version}
      onCancel={goDetail}
    />
  );
}
