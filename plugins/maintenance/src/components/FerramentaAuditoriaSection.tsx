import { useCallback, useEffect, useState } from "react";

import { auditActionLabel, auditPayloadSummary, formatAuditUser } from "../content/auditLabels";
import { fetchFerramentaAuditoria, type FerramentaAuditItem } from "../data/api/maintenanceApi";
import { useServerTable } from "../hooks/useServerTable";
import { DataTableSection, type DataTableColumn } from "./data";

type FerramentaAuditoriaSectionProps = {
  filial: string;
  codigoFerramenta: string;
  reloadKey?: number;
  getAccessToken?: () => string | undefined;
};

function formatDateTime(value?: string | null) {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return parsed.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const auditColumns: DataTableColumn<FerramentaAuditItem>[] = [
  {
    key: "data",
    header: "Quando",
    sortable: false,
    render: (item) => formatDateTime(item.data_criacao),
  },
  {
    key: "acao",
    header: "Ação",
    sortable: false,
    render: (item) => auditActionLabel(item.acao),
  },
  {
    key: "detalhe",
    header: "Detalhe",
    sortable: false,
    render: (item) => auditPayloadSummary(item.payload),
  },
  {
    key: "usuario",
    header: "Usuário",
    sortable: false,
    render: (item) => {
      const label = formatAuditUser(item.usuario_nome, item.usuario_sub);
      const id = item.usuario_sub?.trim();
      if (item.usuario_nome?.trim() && id) {
        return <span title={id}>{label}</span>;
      }
      return label;
    },
  },
];

export function FerramentaAuditoriaSection({
  filial,
  codigoFerramenta,
  reloadKey = 0,
  getAccessToken,
}: FerramentaAuditoriaSectionProps) {
  const auditTable = useServerTable({ pageSize: 10 });
  const [items, setItems] = useState<FerramentaAuditItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAuditoria = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchFerramentaAuditoria(
        {
          filial,
          codigoFerramenta,
          page: auditTable.query.page,
          pageSize: auditTable.query.pageSize,
        },
        getAccessToken,
      );
      setItems(data.items ?? []);
      setTotal(data.total ?? 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar auditoria.");
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [
    auditTable.query.page,
    auditTable.query.pageSize,
    codigoFerramenta,
    filial,
    getAccessToken,
  ]);

  useEffect(() => {
    void loadAuditoria();
  }, [loadAuditoria, reloadKey]);

  return (
    <>
      {error ? <p className="dm-inline-error">{error}</p> : null}
      <DataTableSection
        columnPreferencesKey="maintenance:FerramentaAuditoriaSection:auditoria-da-ferramenta:v1"
        title="Auditoria da ferramenta"
        titleHint="Registro cronológico de reposições e revisões programadas desta ferramenta."
        countBadgeLabel="evento(s)"
        columns={auditColumns}
        rows={items}
        loading={loading}
        emptyMessage="Nenhum evento registrado para esta ferramenta."
        getRowKey={(item) => item.audit_id}
        serverTable={{
          page: auditTable.query.page,
          pageSize: auditTable.query.pageSize,
          total,
          onPageChange: auditTable.setPage,
          sortKey: auditTable.query.sortKey,
          sortDirection: auditTable.query.sortDirection,
          onSortChange: auditTable.handleSortChange,
        }}
      />
    </>
  );
}
