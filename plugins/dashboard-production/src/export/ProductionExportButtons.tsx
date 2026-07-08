import { TabularExportButtons } from "@delpi/plugin-ui";

import { runProductionExport } from "./dispatch";
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

export type ProductionExportButtonsProps = TableExportButtonsProps | DashboardExportButtonsProps;

function dispatchRequest(
  props: ProductionExportButtonsProps,
  format: TabularExportFormat,
): void {
  if (props.variant === "table") {
    void (async () => {
      const payload = props.resolvePayload ? await props.resolvePayload() : props.payload;
      runProductionExport({ kind: "table", payload, format });
    })();
    return;
  }

  void (async () => {
    const context = props.resolveContext ? await props.resolveContext() : props.context;
    runProductionExport({ kind: "dashboard", context, format });
  })();
}

export function ProductionExportButtons(props: ProductionExportButtonsProps) {
  const {
    disabled = false,
    className = "dp-export-actions",
    buttonClassName = "dp-ghost-btn dp-export-actions__btn",
    showIcon = true,
  } = props;

  return (
    <TabularExportButtons
      disabled={disabled}
      className={className}
      buttonClassName={buttonClassName}
      showIcon={showIcon}
      onExport={(format) => dispatchRequest(props, format)}
    />
  );
}
