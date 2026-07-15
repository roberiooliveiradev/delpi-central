import type { ReactNode } from "react";
import { Download, FileSpreadsheet, FileText } from "lucide-react";

import { TABULAR_EXPORT_ACTIONS, type ExportAction, type TabularExportFormat } from "./types";

export type TabularExportButtonsProps = {
  /** Ações exibidas (default: CSV / Excel / PDF). */
  actions?: ReadonlyArray<ExportAction>;
  disabled?: boolean;
  /** Desabilita e troca rótulo enquanto exporta (padrão jsPDF / download longo). */
  exporting?: boolean;
  className?: string;
  buttonClassName?: string;
  showIcon?: boolean;
  groupAriaLabel?: string;
  exportingLabel?: string;
  /** Conteúdo à esquerda (ex.: rótulo "Exportar" no CX). */
  leading?: ReactNode;
  onExport: (format: TabularExportFormat) => void | Promise<void>;
};

/**
 * Grupo CSV · Excel · PDF usado pelos dashboards departamentais.
 * Classes BEM e ícone ficam no consumidor (prefixo do plugin).
 */
export function TabularExportButtons({
  actions = TABULAR_EXPORT_ACTIONS,
  disabled = false,
  exporting = false,
  className = "delpi-ui-export-actions",
  buttonClassName = "delpi-ui-export-actions__btn",
  showIcon = true,
  groupAriaLabel = "Exportar dados",
  exportingLabel = "Exportando…",
  leading = null,
  onExport,
}: TabularExportButtonsProps) {
  const isDisabled = disabled || exporting;

  return (
    <div className={className} role="group" aria-label={groupAriaLabel}>
      {leading}
      {actions.map((action) => (
        <button
          key={action.format}
          type="button"
          className={buttonClassName}
          title={action.title}
          aria-label={action.title}
          disabled={isDisabled}
          aria-busy={exporting || undefined}
          onClick={() => void onExport(action.format)}
        >
          {showIcon ? <Download size={15} aria-hidden="true" /> : null}
          <span>{exporting ? exportingLabel : action.label}</span>
        </button>
      ))}
    </div>
  );
}

export type DocumentExportActionsProps = {
  disabled?: boolean;
  exporting?: boolean;
  onExportExcel: () => void | Promise<void>;
  onExportPdf: () => void | Promise<void>;
  className?: string;
  buttonClassName?: string;
  excelLabel?: string;
  pdfLabel?: string;
  exportingLabel?: string;
};

/**
 * Par Excel + PDF (ícones spreadsheet/file) — production / eficiência-fabril.
 */
export function DocumentExportActions({
  disabled = false,
  exporting = false,
  onExportExcel,
  onExportPdf,
  className = "delpi-ui-export-actions",
  buttonClassName = "delpi-ui-ghost-btn",
  excelLabel = "Excel",
  pdfLabel = "PDF",
  exportingLabel = "Exportando…",
}: DocumentExportActionsProps) {
  const isDisabled = disabled || exporting;

  return (
    <div className={className} role="group" aria-label="Exportar documento">
      <button
        type="button"
        className={buttonClassName}
        onClick={() => void onExportExcel()}
        disabled={isDisabled}
        aria-busy={exporting || undefined}
      >
        <FileSpreadsheet size={16} aria-hidden="true" />
        {exporting ? exportingLabel : excelLabel}
      </button>
      <button
        type="button"
        className={buttonClassName}
        onClick={() => void onExportPdf()}
        disabled={isDisabled}
        aria-busy={exporting || undefined}
      >
        <FileText size={16} aria-hidden="true" />
        {pdfLabel}
      </button>
    </div>
  );
}

export type ExcelExportButtonProps = {
  disabled?: boolean;
  exporting?: boolean;
  onExport: () => void | Promise<void>;
  className?: string;
  buttonClassName?: string;
  label?: string;
  exportingLabel?: string;
};

/** Botão único Excel — controle-retrabalhos / outliers. */
export function ExcelExportButton({
  disabled = false,
  exporting = false,
  onExport,
  className = "delpi-ui-export-actions",
  buttonClassName = "delpi-ui-ghost-btn",
  label = "Excel",
  exportingLabel = "Exportando…",
}: ExcelExportButtonProps) {
  const isDisabled = disabled || exporting;

  return (
    <div className={className} role="group" aria-label="Exportar Excel">
      <button
        type="button"
        className={buttonClassName}
        onClick={() => void onExport()}
        disabled={isDisabled}
        aria-busy={exporting || undefined}
      >
        <FileSpreadsheet size={16} aria-hidden="true" />
        {exporting ? exportingLabel : label}
      </button>
    </div>
  );
}

export function createDashboardTabularExportButtons(config: {
  prefix: string;
  groupAriaLabel?: string;
  compactModifier?: string;
}) {
  const prefix = config.prefix;
  const defaultClassName = `${prefix}-export-actions delpi-ui-export-actions`;
  const defaultButtonClassName = `${prefix}-ghost-btn ${prefix}-export-actions__btn delpi-ui-ghost-btn delpi-ui-export-actions__btn`;

  return function DashboardTabularExportButtons(
    props: Omit<TabularExportButtonsProps, "className" | "buttonClassName"> & {
      className?: string;
      buttonClassName?: string;
      compact?: boolean;
    },
  ) {
    const {
      compact = false,
      className = compact
        ? `${defaultClassName} ${prefix}-export-actions--compact delpi-ui-export-actions--compact`
        : defaultClassName,
      buttonClassName = defaultButtonClassName,
      groupAriaLabel = config.groupAriaLabel,
      ...rest
    } = props;

    return (
      <TabularExportButtons
        className={className}
        buttonClassName={buttonClassName}
        groupAriaLabel={groupAriaLabel}
        {...rest}
      />
    );
  };
}
