import { GHOST_BTN } from "../ui/ghostChrome";
/**
 * UI genérica CSV/Excel/PDF — domínio e builders permanecem em `dispatch` / builders.
 */
import { TabularExportButtons } from "@delpi/plugin-ui/index";

import { runLmpsExport } from "./dispatch";
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

export type LmpsExportButtonsProps = TableExportButtonsProps | DashboardExportButtonsProps;

function dispatchRequest(props: LmpsExportButtonsProps, format: TabularExportFormat): void {
  if (props.variant === "table") {
    void (async () => {
      const payload = props.resolvePayload ? await props.resolvePayload() : props.payload;
      runLmpsExport({ kind: "table", payload, format });
    })();
    return;
  }

  void (async () => {
    const context = props.resolveContext ? await props.resolveContext() : props.context;
    runLmpsExport({ kind: "dashboard", context, format });
  })();
}

export function LmpsExportButtons(props: LmpsExportButtonsProps) {
  const {
    disabled = false,
    className = "lmps-export-actions",
    buttonClassName = `${GHOST_BTN} lmps-export-actions__btn`,
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
