import { TabularExportButtons } from "@delpi/plugin-ui";

import { runCommercialExport } from "./dispatch";
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
    <TabularExportButtons
      disabled={disabled}
      className={className}
      buttonClassName={buttonClassName}
      showIcon={showIcon}
      onExport={(format) => dispatchRequest(props, format)}
    />
  );
}
