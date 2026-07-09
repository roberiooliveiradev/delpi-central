import type { DocxPreviewData } from "./docxPreviewModel";
import type { FilePreviewLabels } from "./filePreviewTypes";
import { DEFAULT_FILE_PREVIEW_LABELS } from "./filePreviewTypes";

type Props = {
  data: DocxPreviewData;
  title?: string;
  labels?: Partial<FilePreviewLabels>;
};

export function DocxPreview({ data, title, labels: labelsProp }: Props) {
  const labels = { ...DEFAULT_FILE_PREVIEW_LABELS, ...labelsProp };
  return (
    <div
      className="delpi-ui-docx-preview"
      role="region"
      aria-label="Pré-visualização do documento somente leitura"
    >
      <div className="delpi-ui-docx-preview__chrome">
        <div className="delpi-ui-docx-preview__titlebar">
          <span className="delpi-ui-docx-preview__title">{labels.docxWordTitle}</span>
          <span className="delpi-ui-docx-preview__badge">{labels.docxReadOnly}</span>
        </div>
        <div className="delpi-ui-docx-preview__toolbar" aria-hidden="true">
          <span className="delpi-ui-docx-preview__toolbar-group">Arquivo</span>
          <span className="delpi-ui-docx-preview__toolbar-group">Exibir</span>
          <span className="delpi-ui-docx-preview__toolbar-doc">
            {title ?? "Documento"}
          </span>
        </div>
      </div>

      <div className="delpi-ui-docx-preview__viewport">
        <article
          className="delpi-ui-docx-preview__page"
          dangerouslySetInnerHTML={{ __html: data.html }}
        />
      </div>

      {data.truncated ? (
        <p className="delpi-ui-file-preview__muted delpi-ui-docx-preview__truncated">
          {labels.docxTruncated}
        </p>
      ) : null}
    </div>
  );
}
