import type { ChatPresentation } from "../../data/api/chatTypes";
import { exportPresentation } from "./presentation/export/exportUtils";

type ExportFormat = "csv" | "xlsx" | "pdf";

const EXPORT_ACTIONS: Array<{ format: ExportFormat; label: string; title: string }> = [
  { format: "csv", label: "↓ CSV", title: "Baixar CSV" },
  { format: "xlsx", label: "↓ Excel", title: "Baixar Excel" },
  { format: "pdf", label: "↓ PDF", title: "Baixar PDF" },
];

export function ChatPresentationExportButtons({
  presentation,
  buttonClassName = "mdc-rich-table__btn",
  tableRows,
  chartRoot,
  getChartRoot,
}: {
  presentation: ChatPresentation;
  buttonClassName?: string;
  tableRows?: Record<string, unknown>[];
  chartRoot?: HTMLElement | null;
  getChartRoot?: () => HTMLElement | null;
}) {
  return (
    <>
      {EXPORT_ACTIONS.map((action) => (
        <button
          key={action.format}
          type="button"
          className={buttonClassName}
          title={action.title}
          onClick={() =>
            exportPresentation(presentation, action.format, {
              tableRows,
              chartRoot: getChartRoot?.() ?? chartRoot ?? null,
            })
          }
        >
          {action.label}
        </button>
      ))}
    </>
  );
}
