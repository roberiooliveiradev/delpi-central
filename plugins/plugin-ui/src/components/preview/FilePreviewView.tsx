import type { ReactNode } from "react";

import { DocxPreview } from "./DocxPreview";
import {
  DEFAULT_FILE_PREVIEW_LABELS,
  type FilePreviewContentState,
  type FilePreviewLabels,
} from "./filePreviewTypes";
import { SpreadsheetPreview } from "./SpreadsheetPreview";

export type FilePreviewViewProps = {
  state: FilePreviewContentState;
  title?: string;
  labels?: Partial<FilePreviewLabels>;
  className?: string;
  footer?: ReactNode;
};

function resolveLabels(labels?: Partial<FilePreviewLabels>): FilePreviewLabels {
  return { ...DEFAULT_FILE_PREVIEW_LABELS, ...labels };
}

function resolveErrorMessage(error: string, labels: FilePreviewLabels): string {
  if (error === "empty") return labels.emptyText;
  if (error === "unsupported") return labels.unavailable;
  if (error === "load_failed") return labels.loadFailed;
  return error;
}

/** Render-only — consumir com `useFilePreviewLoader` ou estado montado pelo plugin. */
export function FilePreviewView({
  state,
  title,
  labels: labelsProp,
  className,
  footer,
}: FilePreviewViewProps) {
  const labels = resolveLabels(labelsProp);

  if (state.loading) {
    return (
      <p className={["delpi-ui-file-preview__status", className].filter(Boolean).join(" ")}>
        {labels.loading}
      </p>
    );
  }

  if (state.error) {
    return (
      <p className={["delpi-ui-file-preview__status", className].filter(Boolean).join(" ")}>
        {resolveErrorMessage(state.error, labels)}
      </p>
    );
  }

  if (state.kind === "image" && state.previewUrl) {
    return (
      <>
        <img
          src={state.previewUrl}
          alt={title ?? "Pré-visualização"}
          className="delpi-ui-file-preview__image"
        />
        {footer}
      </>
    );
  }

  if (state.kind === "pdf" && state.previewUrl) {
    return (
      <>
        <iframe
          src={state.previewUrl}
          title={title ? `Pré-visualização: ${title}` : "Pré-visualização PDF"}
          className="delpi-ui-file-preview__pdf"
        />
        {footer}
      </>
    );
  }

  if (state.spreadsheetData) {
    return (
      <>
        <SpreadsheetPreview data={state.spreadsheetData} labels={labels} />
        {footer}
      </>
    );
  }

  if (state.docxData) {
    return (
      <>
        <DocxPreview data={state.docxData} title={title} labels={labels} />
        {footer}
      </>
    );
  }

  if (state.textContent) {
    return (
      <>
        <div className="delpi-ui-file-preview__text-wrap">
          <pre className="delpi-ui-file-preview__text">{state.textContent}</pre>
          {state.textTruncated ? (
            <p className="delpi-ui-file-preview__muted delpi-ui-file-preview__truncated">
              {labels.textTruncated}
            </p>
          ) : null}
        </div>
        {footer}
      </>
    );
  }

  return (
    <p className={["delpi-ui-file-preview__status", className].filter(Boolean).join(" ")}>
      {labels.unavailable}
    </p>
  );
}
