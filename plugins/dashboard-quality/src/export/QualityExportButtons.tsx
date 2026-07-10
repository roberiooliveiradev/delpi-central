import { TabularExportButtons } from "@delpi/plugin-ui/index";

import { runQualityExport } from "./dispatch";
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

export type QualityExportButtonsProps = TableExportButtonsProps | DashboardExportButtonsProps;

function dispatchRequest(props: QualityExportButtonsProps, format: TabularExportFormat): void {
  if (props.variant === "table") {
    void (async () => {
      const payload = props.resolvePayload ? await props.resolvePayload() : props.payload;
      runQualityExport({ kind: "table", payload, format });
    })();
    return;
  }

  void (async () => {
    const context = props.resolveContext ? await props.resolveContext() : props.context;
    runQualityExport({ kind: "dashboard", context, format });
  })();
}

export function QualityExportButtons(props: QualityExportButtonsProps) {
  const {
    disabled = false,
    className = "dq-export-actions",
    buttonClassName = "dq-ghost-btn dq-export-actions__btn",
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
