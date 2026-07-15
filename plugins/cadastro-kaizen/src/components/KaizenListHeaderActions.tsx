import { Download, Share2, Upload } from "lucide-react";
import { KZ_GHOST_BTN } from "./ui/ghostChrome";

type ListHeaderActionsProps = {
  onNew: () => void;
  onRefresh: () => void;
  onShare?: () => void;
  onExport?: () => void;
  onImport?: () => void;
  loading?: boolean;
  exporting?: boolean;
  importing?: boolean;
};

export function KaizenListHeaderActions({
  onNew,
  onRefresh,
  onShare,
  onExport,
  onImport,
  loading,
  exporting,
  importing,
}: ListHeaderActionsProps) {
  return (
    <>
      {onShare ? (
        <button type="button" className={KZ_GHOST_BTN} onClick={onShare}>
          <Share2 size={16} aria-hidden="true" />
          Compartilhar
        </button>
      ) : null}
      {onExport ? (
        <button
          type="button"
          className={KZ_GHOST_BTN}
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
          className={KZ_GHOST_BTN}
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
        className={KZ_GHOST_BTN}
        onClick={onRefresh}
        disabled={loading}
      >
        {loading ? "Atualizando…" : "Atualizar"}
      </button>
    </>
  );
}
