import { Download, Upload } from "lucide-react";

type ListHeaderActionsProps = {
  onNew: () => void;
  onRefresh: () => void;
  onExport?: () => void;
  onImport?: () => void;
  loading?: boolean;
  exporting?: boolean;
  importing?: boolean;
};

export function KaizenListHeaderActions({
  onNew,
  onRefresh,
  onExport,
  onImport,
  loading,
  exporting,
  importing,
}: ListHeaderActionsProps) {
  return (
    <>
      {onExport ? (
        <button
          type="button"
          className="kz-ghost-btn"
          onClick={onExport}
          disabled={exporting}
        >
          <Download size={16} aria-hidden="true" />
          {exporting ? "Exportando…" : "Exportar JSON"}
        </button>
      ) : null}
      {onImport ? (
        <button
          type="button"
          className="kz-ghost-btn"
          onClick={onImport}
          disabled={importing}
        >
          <Upload size={16} aria-hidden="true" />
          {importing ? "Importando…" : "Importar JSON"}
        </button>
      ) : null}
      <button type="button" className="kz-primary-btn" onClick={onNew}>
        Novo kaizen
      </button>
      <button
        type="button"
        className="kz-ghost-btn"
        onClick={onRefresh}
        disabled={loading}
      >
        {loading ? "Atualizando…" : "Atualizar"}
      </button>
    </>
  );
}
