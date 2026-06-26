import { Download } from "lucide-react";

import { runSuppliesExport } from "./dispatch";
import { TABULAR_EXPORT_ACTIONS } from "./types";
import type {
  DashboardExportContext,
  TabularExportFormat,
  TableExportPayload,
} from "./types";

type ExportButtonsBaseProps = {
  disabled?: boolean;
  className?: string;
  buttonClassName?: string;
  showIcon?: boolean;
};

type TableExportButtonsProps = ExportButtonsBaseProps & {
  variant: "table";
  payload: TableExportPayload;
  resolvePayload?: () => Promise<TableExportPayload>;
};

type DashboardExportButtonsProps = ExportButtonsBaseProps & {
  variant: "dashboard";
  context: DashboardExportContext;
  resolveContext?: () => Promise<DashboardExportContext>;
};

export type SuppliesExportButtonsProps = TableExportButtonsProps | DashboardExportButtonsProps;

function dispatchRequest(
  props: SuppliesExportButtonsProps,
  format: TabularExportFormat,
): void {
  if (props.variant === "table") {
    void (async () => {
      const payload = props.resolvePayload
        ? await props.resolvePayload()
        : props.payload;
      runSuppliesExport({
        kind: "table",
        payload,
        format,
      });
    })();
    return;
  }

  void (async () => {
    const context = props.resolveContext
      ? await props.resolveContext()
      : props.context;
    runSuppliesExport({ kind: "dashboard", context, format });
  })();
}

export function SuppliesExportButtons(props: SuppliesExportButtonsProps) {
  const {
    disabled = false,
    className = "ds-export-actions",
    buttonClassName = "ds-ghost-btn ds-export-actions__btn",
    showIcon = true,
  } = props;

  return (
    <div className={className} role="group" aria-label="Exportar dados">
      {TABULAR_EXPORT_ACTIONS.map((action) => (
        <button
          key={action.format}
          type="button"
          className={buttonClassName}
          title={action.title}
          aria-label={action.title}
          disabled={disabled}
          onClick={() => dispatchRequest(props, action.format)}
        >
          {showIcon ? <Download size={15} aria-hidden="true" /> : null}
          <span>{action.label}</span>
        </button>
      ))}
    </div>
  );
}
