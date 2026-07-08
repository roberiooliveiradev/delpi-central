import { TabularExportButtons } from "@delpi/plugin-ui";

import { runEngineeringExport } from "./dispatch";
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

export type EngineeringExportButtonsProps = TableExportButtonsProps | DashboardExportButtonsProps;

function dispatchRequest(props: EngineeringExportButtonsProps, format: TabularExportFormat): void {
  if (props.variant === "table") {
    void (async () => {
      const payload = props.resolvePayload ? await props.resolvePayload() : props.payload;
      runEngineeringExport({ kind: "table", payload, format });
    })();
    return;
  }

  void (async () => {
    const context = props.resolveContext ? await props.resolveContext() : props.context;
    runEngineeringExport({ kind: "dashboard", context, format });
  })();
}

export function EngineeringExportButtons(props: EngineeringExportButtonsProps) {
  const {
    disabled = false,
    className = "ds-export-actions",
    buttonClassName = "ds-ghost-btn ds-export-actions__btn",
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
