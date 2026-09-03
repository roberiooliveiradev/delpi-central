import { useEffect, useMemo, useState } from "react";
import { ActionButton, DataTable, type DataTableColumn } from "@delpi/plugin-ui/index";

import { listWorkQueue } from "../api/requestsApi";
import { AppShell } from "../components/AppShell";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import type { RequestSummary } from "../types/requests";
import {
  MyRequestsEmptyState,
  MyRequestsLoadingState,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  MyRequestsStatusBadge,
} from "../ui/mrUi";
import { mrDataTableClassNames, mrDataTableLabels } from "../ui/mrUiContracts";

export function WorkQueuePage() {
  const access = useRequestsPermissions();
  const [items, setItems] = useState<RequestSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const ac = new AbortController();
    listWorkQueue({ signal: ac.signal })
      .then((data) => setItems(data.items || []))
      .catch((err: Error) => {
        if (err.name !== "AbortError") setError(err.message);
      })
      .finally(() => setLoading(false));
    return () => ac.abort();
  }, []);

  const columns = useMemo<DataTableColumn<RequestSummary>[]>(
    () => [
      {
        key: "number",
        header: "Número",
        render: (row) => (
          <ActionButton
            href={`/apps/my-requests/requests/${row.id}`}
            title={`Abrir ${row.request_number}`}
            variant="link"
          >
            {row.request_number}
          </ActionButton>
        ),
      },
      { key: "type", header: "Tipo", render: (row) => row.type_code },
      {
        key: "status",
        header: "Status",
        render: (row) => (
          <MyRequestsStatusBadge label={row.status_alias || row.status} variant="info" />
        ),
      },
      { key: "branch", header: "Filial", render: (row) => row.branch_code || "—" },
    ],
    [],
  );

  return (
    <AppShell
      title="Fila de trabalho"
      canCreate={access.canCreateInvoiceIssuance || access.canManage}
    >
      <MyRequestsSectionCard title="Pendências">
        <div data-help="work-queue" title={MY_REQUESTS_HELP_TOOLTIPS.workQueue.section}>
          {error ? (
            <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
          ) : null}
          {loading ? <MyRequestsLoadingState /> : null}
          {!loading && !error && items.length === 0 ? (
            <MyRequestsEmptyState message="Fila vazia no momento." />
          ) : null}
          {!loading && items.length > 0 ? (
            <DataTable
              columns={columns}
              rows={items}
              rowKey={(row) => row.id}
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
