import { Download } from "lucide-react";

import { runCommercialExport } from "./dispatch";
import { TABULAR_EXPORT_ACTIONS } from "./types";
import type {
  DashboardExportContext,
  DetailExportContext,
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

type DetailExportButtonsProps = ExportButtonsBaseProps & {
  variant: "detail";
  context: DetailExportContext;
};

export type CommercialExportButtonsProps =
  | TableExportButtonsProps
  | DashboardExportButtonsProps
  | DetailExportButtonsProps;

function dispatchRequest(
  props: CommercialExportButtonsProps,
  format: TabularExportFormat,
): void {
  if (props.variant === "table") {
    void (async () => {
      const payload = props.resolvePayload
        ? await props.resolvePayload()
        : props.payload;
      runCommercialExport({
        kind: "table",
        payload,
        format,
      });
    })();
    return;
  }

  if (props.variant === "dashboard") {
    void (async () => {
      const context = props.resolveContext
        ? await props.resolveContext()
        : props.context;
      runCommercialExport({ kind: "dashboard", context, format });
    })();
    return;
  }

  runCommercialExport({ kind: "detail", context: props.context, format });
}

export function CommercialExportButtons(props: CommercialExportButtonsProps) {
  const {
    disabled = false,
    className = "dc-export-actions",
    buttonClassName = "dc-ghost-btn dc-export-actions__btn",
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
