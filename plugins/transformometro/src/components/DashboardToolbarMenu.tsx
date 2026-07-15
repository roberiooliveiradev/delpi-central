import { ChevronDown, Database, Download, FileDown } from "lucide-react";
import { DS_GHOST_BTN } from "./ghostChrome";

type Props = {
  exporting: "csv" | "excel" | null;
  recalculating: boolean;
  disabled?: boolean;
  onExportCsv: () => void;
  onExportExcel: () => void;
  onRecalcCache: () => void;
};

export function DashboardToolbarMenu({
  exporting,
  recalculating,
  disabled = false,
  onExportCsv,
  onExportExcel,
  onRecalcCache,
}: Props) {
  const busy = disabled || exporting !== null || recalculating;

  return (
    <details className="ds-header-menu">
      <summary className={DS_GHOST_BTN} aria-label="Exportar dados e manutenção do cache">
        <Download size={16} />
        Exportar
        <ChevronDown size={14} className="ds-header-menu__chevron" aria-hidden="true" />
      </summary>
      <div className="ds-header-menu__panel" role="menu">
        <button
          type="button"
          className="ds-header-menu__item"
          role="menuitem"
          disabled={busy}
          onClick={onExportCsv}
        >
          <Download size={15} />
          {exporting === "csv" ? "Gerando CSV…" : "Baixar CSV"}
        </button>
        <button
          type="button"
          className="ds-header-menu__item"
          role="menuitem"
          disabled={busy}
          onClick={onExportExcel}
        >
          <FileDown size={15} />
          {exporting === "excel" ? "Gerando Excel…" : "Baixar Excel"}
        </button>
        <div className="ds-header-menu__divider" role="separator" />
        <button
          type="button"
          className="ds-header-menu__item"
          role="menuitem"
          disabled={busy}
          onClick={onRecalcCache}
        >
          <Database size={15} />
          {recalculating ? "Recalculando cache…" : "Recalcular cache"}
        </button>
        <p className="ds-header-menu__hint">
          O cache alimenta integrações e rotas snapshot; o dashboard usa cálculo em tempo real.
        </p>
      </div>
    </details>
  );
}
