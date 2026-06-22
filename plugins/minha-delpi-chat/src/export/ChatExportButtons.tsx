import { Download } from "lucide-react";

import type { ChatPresentation } from "../data/api/chatTypes";
import type { DrawingAnalysisExportPayload } from "../ui/utils/drawingAnalysisExport";
import { runChatExport, resolveDrawingExportActions } from "./dispatch";
import { PRESENTATION_EXPORT_ACTIONS } from "./types";
import type { TabularExportFormat } from "./types";

type PresentationExportButtonsProps = {
  variant: "presentation";
  presentation: ChatPresentation;
  buttonClassName?: string;
  tableRows?: Record<string, unknown>[];
  chartRoot?: HTMLElement | null;
  getChartRoot?: () => HTMLElement | null;
};

type DrawingExportButtonsProps = {
  variant: "drawing";
  exportPayload: DrawingAnalysisExportPayload;
  drawingAnalysis?: Record<string, unknown>;
  containerClassName?: string;
  buttonClassName?: string;
  showIcon?: boolean;
};

export type ChatExportButtonsProps = PresentationExportButtonsProps | DrawingExportButtonsProps;

export function ChatExportButtons(props: ChatExportButtonsProps) {
  if (props.variant === "presentation") {
    const {
      presentation,
      buttonClassName = "mdc-rich-table__btn",
      tableRows,
      chartRoot,
      getChartRoot,
    } = props;

    return (
      <>
        {PRESENTATION_EXPORT_ACTIONS.map((action) => (
          <button
            key={action.format}
            type="button"
            className={buttonClassName}
            title={action.title}
            onClick={() =>
              runChatExport({
                kind: "presentation",
                presentation,
                format: action.format as TabularExportFormat,
                options: {
                  tableRows,
                  chartRoot: getChartRoot?.() ?? chartRoot ?? null,
                },
              })
            }
          >
            {action.label}
          </button>
        ))}
      </>
    );
  }

  const {
    exportPayload,
    drawingAnalysis,
    containerClassName = "mdc-chat-drawing-export",
    buttonClassName = "mdc-chat-message-action mdc-chat-drawing-export__btn",
    showIcon = true,
  } = props;

  const actions = resolveDrawingExportActions(exportPayload);

  if (!actions.length) {
    return null;
  }

  return (
    <div className={containerClassName}>
      {actions.map((action) => (
        <button
          key={action.format}
          type="button"
          className={buttonClassName}
          title={action.title}
          aria-label={action.title}
          onClick={() =>
            runChatExport({
              kind: "drawing",
              payload: exportPayload,
              format: action.format as "pdf" | "markdown" | "csv" | "xlsx",
              drawingAnalysis,
            })
          }
        >
          {showIcon ? <Download size={15} aria-hidden="true" /> : null}
          <span>{action.label}</span>
        </button>
      ))}
    </div>
  );
}

/** Compatibilidade com toolbar de apresentação rica existente. */
export function ChatPresentationExportButtons(
  props: Omit<PresentationExportButtonsProps, "variant">,
) {
  return <ChatExportButtons variant="presentation" {...props} />;
}

/** Barra de exportação do relatório de análise de desenho. */
export function ChatDrawingExportButtons(
  props: Omit<DrawingExportButtonsProps, "variant">,
) {
  return <ChatExportButtons variant="drawing" {...props} />;
}
