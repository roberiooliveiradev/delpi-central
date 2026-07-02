import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { FolderOpen, Trash2 } from "lucide-react";

import {
  deleteKaizenRecord,
  exportKaizenRecords,
  fetchKaizenRecords,
  importKaizenRecords,
  type KaizenExportFile,
} from "../api/kaizenApi";
import type { DataTableColumn } from "../components/data/DataTable";
import { DataTableSection } from "../components/data/DataTableSection";
import {
  KaizenListHeaderActions,
  KaizenPageHeader,
} from "../components/KaizenPageHeader";
import { KaizenNavTabs } from "../components/KaizenNavTabs";
import { KaizenRecordFilters } from "../components/KaizenRecordFilters";
import { StateAlert } from "../components/StateAlert";
import { detailPath, newPath } from "../constants/kaizen";
import type { KaizenRecord } from "../types/kaizen";
import { formatCurrency } from "../utils/format";
import { savingsTypeLabel, statusLabel, unitLabel } from "../utils/labels";

type Props = {
  onNavigate: (path: string) => void;
};

export function KaizenListPage({ onNavigate }: Props) {
  const [items, setItems] = useState<KaizenRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
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

  const handleExport = useCallback(async () => {
    setExporting(true);
    setError(null);
    setSuccess(null);
    try {
      const data = await exportKaizenRecords();
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `kaizens-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setSuccess(`Exportação concluída: ${data.count} kaizen(s) no arquivo.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao exportar kaizens.");
    } finally {
      setExporting(false);
    }
  }, []);

  const handleImportFile = useCallback(
    async (file: File) => {
      setImporting(true);
      setError(null);
      setSuccess(null);
      try {
        const text = await file.text();
        const parsed = JSON.parse(text) as KaizenExportFile | Array<Record<string, unknown>>;
        const items = Array.isArray(parsed) ? parsed : parsed.items;
        if (!Array.isArray(items) || items.length === 0) {
          throw new Error("Arquivo JSON sem kaizens (campo \"items\" vazio).");
        }
        const result = await importKaizenRecords(items);
        setSuccess(
          `Importação concluída: ${result.created} criado(s), ${result.skipped} ignorado(s), ${result.errors} erro(s).`,
        );
        await load();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Erro ao importar kaizens do arquivo JSON.",
        );
      } finally {
        setImporting(false);
      }
    },
    [load],
  );

  const handleFileChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      event.target.value = "";
      if (file) void handleImportFile(file);
    },
    [handleImportFile],
  );

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
      { key: "branch", header: "Unidade", render: (row) => unitLabel(row.branch_code) },
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
              onClick={() => onNavigate(detailPath(row.id))}
            >
              <FolderOpen size={14} aria-hidden="true" />
              Abrir
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
        nav={<KaizenNavTabs active="list" onNavigate={onNavigate} />}
        actions={
          <KaizenListHeaderActions
            onNew={() => onNavigate(newPath())}
            onRefresh={() => void load()}
            onExport={() => void handleExport()}
            onImport={() => fileInputRef.current?.click()}
            loading={loading}
            exporting={exporting}
            importing={importing}
          />
        }
      />

      <input
        ref={fileInputRef}
        type="file"
        accept="application/json,.json"
        style={{ display: "none" }}
        onChange={handleFileChange}
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
            unitLabel(row.branch_code),
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
