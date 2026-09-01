import { useEffect, useMemo, useState } from "react";

import { fetchDeviceCommands } from "../../api/productionPulseApi";
import { PpActionButton, PpPagination, PpSectionCard } from "../../app/productionPulseUi";
import { PpDataTable, type DataTableColumn } from "../data/dataTableUi";
import type { DeviceCommandAudit } from "../../types/detail";
import { PP_HELP } from "../../content/helpTooltips";
import { useViewportBucket } from "../../hooks/useViewportBucket";
import { commandLabel, formatDateTime } from "../../utils/detailDisplay";
import { CommandAuditCard } from "./CommandAuditCard";
import { CommandJsonModal } from "../modals/CommandJsonModal";

const PAGE_SIZE = 20;

type DeviceCommandsTabProps = {
  deviceId: string;
  refreshToken: number;
};

export function DeviceCommandsTab({ deviceId, refreshToken }: DeviceCommandsTabProps) {
  const viewport = useViewportBucket();
  const isMobile = viewport === "mobile";
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [commands, setCommands] = useState<DeviceCommandAudit[]>([]);
  const [total, setTotal] = useState(0);
  const [jsonModal, setJsonModal] = useState<DeviceCommandAudit | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    fetchDeviceCommands(deviceId, { page, pageSize: PAGE_SIZE, signal: controller.signal })
      .then((payload) => {
        setCommands(payload.items);
        setTotal(payload.pagination.total);
        setLoading(false);
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar comandos.");
        setLoading(false);
      });
    return () => controller.abort();
  }, [deviceId, page, refreshToken]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const columns = useMemo<DataTableColumn<DeviceCommandAudit>[]>(
    () => [
      {
        key: "createdAt",
        header: "Data/hora",
        render: (row) => formatDateTime(row.createdAt),
      },
      {
        key: "commandKey",
        header: "Comando",
        render: (row) => commandLabel(row.commandKey),
      },
      {
        key: "issuedBy",
        header: "Usuário",
        render: (row) => row.issuedBy || "—",
      },
      {
        key: "success",
        header: "Resultado",
        render: (row) => (row.success ? "OK" : "Falha"),
      },
      {
        key: "detail",
        header: "Detalhe",
        render: (row) => row.errorMessage || "—",
      },
      {
        key: "json",
        header: "",
        interactive: true,
        render: (row) => (
          <PpActionButton variant="ghost" onClick={() => setJsonModal(row)}>
            Ver JSON
          </PpActionButton>
        ),
      },
    ],
    [],
  );

  return (
    <>
      <PpSectionCard title="Auditoria de comandos" hint={PP_HELP.detail.commandsTable}>
        {error ? <p className="pp-detail-error">{error}</p> : null}
        {isMobile ? (
          <div className="pp-command-card-list">
            {commands.map((command) => (
              <CommandAuditCard key={command.id} command={command} onViewJson={setJsonModal} />
            ))}
            {commands.length === 0 && !loading ? (
              <p className="pp-detail-muted">Nenhum comando registrado.</p>
            ) : null}
          </div>
        ) : (
          <PpDataTable
            columns={columns}
            rows={commands}
            loading={loading}
            rowKey={(row) => row.id}
            emptyMessage="Nenhum comando registrado."
          />
        )}
        <PpPagination
          page={page}
          pageSize={PAGE_SIZE}
          total={total}
          totalPages={totalPages}
          onPageChange={setPage}
          hideWhenSinglePage
        />
      </PpSectionCard>

      <CommandJsonModal
        open={jsonModal != null}
        title="Resposta do comando"
        payload={jsonModal?.responsePayload ?? {}}
        onClose={() => setJsonModal(null)}
      />
    </>
  );
}
