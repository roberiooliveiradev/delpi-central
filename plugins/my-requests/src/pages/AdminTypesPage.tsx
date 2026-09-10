import { useEffect, useMemo, useState } from "react";
import { DataTable, type DataTableColumn } from "@delpi/plugin-ui/index";

import { listRequestTypes } from "../api/requestsApi";
import { AppShell } from "../components/AppShell";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  branchScopeLabel,
  presentationModeLabel,
} from "../content/presentationLabels";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import type { RequestTypeSummary } from "../types/requests";
import {
  MyRequestsEmptyState,
  MyRequestsLoadingState,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  MyRequestsStatusBadge,
} from "../ui/mrUi";
import { mrDataTableClassNames, mrDataTableLabels } from "../ui/mrUiContracts";

export function AdminTypesPage() {
  const access = useRequestsPermissions();
  const [items, setItems] = useState<RequestTypeSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!access.canManage) {
      setLoading(false);
      return;
    }
    const ac = new AbortController();
    setLoading(true);
    setError(null);
    listRequestTypes({ signal: ac.signal })
      .then(setItems)
      .catch((err: Error) => {
        if (err.name !== "AbortError") setError(err.message);
      })
      .finally(() => setLoading(false));
    return () => ac.abort();
  }, [access.canManage]);

  const columns = useMemo<DataTableColumn<RequestTypeSummary>[]>(
    () => [
      { key: "code", header: "Código", render: (row) => row.code },
      { key: "name", header: "Nome", render: (row) => row.name },
      {
        key: "active",
        header: "Ativo",
        render: (row) => (
          <MyRequestsStatusBadge
            label={row.active === false ? "Inativo" : "Ativo"}
            variant={row.active === false ? "warning" : "info"}
          />
        ),
      },
      {
        key: "branch",
        header: "Filial",
        render: (row) => branchScopeLabel(row.branch_scope),
      },
      {
        key: "presentation",
        header: "Formulário",
        render: (row) => presentationModeLabel(row.presentation_mode),
      },
    ],
    [],
  );

  return (
    <AppShell title="Tipos de solicitação">
      <MyRequestsSectionCard title="Catálogo de tipos">
        <div data-help="admin" title={MY_REQUESTS_HELP_TOOLTIPS.admin.section}>
          {!access.canManage ? (
            <MyRequestsStateBanner variant="error">
              Você não tem permissão para administrar tipos de solicitação.
            </MyRequestsStateBanner>
          ) : null}
          {access.canManage && error ? (
            <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
          ) : null}
          {access.canManage && loading ? <MyRequestsLoadingState /> : null}
          {access.canManage && !loading && !error && items.length === 0 ? (
            <MyRequestsEmptyState message="Nenhum tipo cadastrado." />
          ) : null}
          {access.canManage && !loading && items.length > 0 ? (
            <DataTable
              columns={columns}
              rows={items}
              rowKey={(row) => row.code}
              layout="embedded"
              classNames={mrDataTableClassNames}
              labels={mrDataTableLabels}
            />
          ) : null}
        </div>
      </MyRequestsSectionCard>
    </AppShell>
  );
}
