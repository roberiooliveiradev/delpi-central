import { useCallback, useEffect, useMemo, useState } from "react";
import { Pencil, Trash2 } from "lucide-react";

import { deleteKaizenRecord, fetchKaizenRecords, importKaizensFromSheet } from "../api/kaizenApi";
import type { DataTableColumn } from "../components/data/DataTable";
import { DataTableSection } from "../components/data/DataTableSection";
import {
  KaizenListHeaderActions,
  KaizenPageHeader,
} from "../components/KaizenPageHeader";
import { KaizenRecordFilters } from "../components/KaizenRecordFilters";
import { StateAlert } from "../components/StateAlert";
import { editPath, newPath } from "../constants/kaizen";
import type { KaizenRecord } from "../types/kaizen";
import { formatCurrency } from "../utils/format";
import { savingsTypeLabel, statusLabel } from "../utils/labels";

type Props = {
  onNavigate: (path: string) => void;
};

export function KaizenListPage({ onNavigate }: Props) {
  const [items, setItems] = useState<KaizenRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [branch, setBranch] = useState("");
  const [status, setStatus] = useState("");
  const [savingsType, setSavingsType] = useState("");
  const [title, setTitle] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchKaizenRecords({
        branch: branch || undefined,
        status: status || undefined,
        savings_type: savingsType || undefined,
        title: title || undefined,
        page_size: 200,
      });
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar kaizens.");
    } finally {
      setLoading(false);
    }
  }, [branch, status, savingsType, title]);

  useEffect(() => {
    void load();
  }, [load]);

  const handleImport = useCallback(async () => {
    const confirmed = window.confirm(
      "Importar kaizens ativos da planilha Google Sheets para o PostgreSQL?",
    );
    if (!confirmed) return;

    setImporting(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await importKaizensFromSheet();
      setSuccess(
        `Importação concluída: ${result.created} criado(s), ${result.skipped} ignorado(s), ${result.errors} erro(s).`,
      );
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao importar kaizens da planilha.");
    } finally {
      setImporting(false);
    }
  }, [load]);

  const handleDelete = useCallback(
    async (record: KaizenRecord) => {
      const confirmed = window.confirm(`Excluir o kaizen "${record.title}"?`);
      if (!confirmed) return;

      try {
        await deleteKaizenRecord(record.id);
        await load();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao excluir kaizen.");
      }
    },
    [load],
  );

  const columns = useMemo<DataTableColumn<KaizenRecord>[]>(
    () => [
      { key: "branch", header: "Filial", render: (row) => row.branch_code },
      { key: "title", header: "Título", render: (row) => row.title },
      { key: "accountable", header: "Responsável", render: (row) => row.accountable ?? "—" },
      {
        key: "savings_type",
        header: "Tipo economia",
        render: (row) => savingsTypeLabel(row.savings_type),
      },
      {
        key: "daily_savings",
        header: "Economia/dia",
        className: "kz-table__col--numeric",
        render: (row) => formatCurrency(row.daily_savings),
      },
      {
        key: "annual_savings",
        header: "Economia/ano",
        className: "kz-table__col--numeric",
        render: (row) => formatCurrency(row.annual_savings),
      },
      {
        key: "status",
        header: "Status",
        render: (row) => statusLabel(row.status),
      },
      {
        key: "date",
        header: "Data",
        render: (row) => row.date_implemented ?? "—",
      },
      {
        key: "actions",
        header: "Ações",
        render: (row) => (
          <div className="kz-row-actions">
            <button
              type="button"
              className="kz-ghost-btn"
              onClick={() => onNavigate(editPath(row.id))}
            >
              <Pencil size={14} aria-hidden="true" />
              Editar
            </button>
            <button
              type="button"
              className="kz-danger-btn"
              onClick={() => void handleDelete(row)}
            >
              <Trash2 size={14} aria-hidden="true" />
            </button>
          </div>
        ),
      },
    ],
    [handleDelete, onNavigate],
  );

  return (
    <>
      <KaizenPageHeader
        title="Cadastro de Kaizens"
        subtitle="Melhorias contínuas — módulo qualidade"
        actions={
          <KaizenListHeaderActions
            onNew={() => onNavigate(newPath())}
            onRefresh={() => void load()}
            onImport={() => void handleImport()}
            loading={loading}
            importing={importing}
          />
        }
      />

      <KaizenRecordFilters
        branch={branch}
        status={status}
        savingsType={savingsType}
        title={title}
        onBranchChange={setBranch}
        onStatusChange={setStatus}
        onSavingsTypeChange={setSavingsType}
        onTitleChange={setTitle}
      />

      {error ? <StateAlert variant="error">{error}</StateAlert> : null}
      {success ? <StateAlert variant="success">{success}</StateAlert> : null}

      <DataTableSection
        title="Kaizens cadastrados"
        hint="Dados persistidos no PostgreSQL"
        columns={columns}
        rows={items}
        rowKey={(row) => row.id}
        loading={loading}
        emptyMessage="Nenhum kaizen cadastrado."
        searchPlaceholder="Buscar na listagem…"
        getSearchText={(row) =>
          [
            row.branch_code,
            row.title,
            row.accountable,
            row.sector,
            savingsTypeLabel(row.savings_type),
            statusLabel(row.status),
          ]
            .filter(Boolean)
            .join(" ")
        }
      />
    </>
  );
}
