import type { DocxPreviewData } from "./docxPreviewModel";

type Props = {
  data: DocxPreviewData;
  title?: string;
};

export function DocxPreview({ data, title }: Props) {
  return (
    <div
      className="pac-docx-preview"
      role="region"
      aria-label="Pré-visualização do documento somente leitura"
    >
      <div className="pac-docx-preview__chrome">
        <div className="pac-docx-preview__titlebar">
          <span className="pac-docx-preview__title">Word</span>
          <span className="pac-docx-preview__badge">Somente leitura</span>
        </div>
        <div className="pac-docx-preview__toolbar" aria-hidden="true">
          <span className="pac-docx-preview__toolbar-group">Arquivo</span>
          <span className="pac-docx-preview__toolbar-group">Exibir</span>
          <span className="pac-docx-preview__toolbar-doc">
            {title ?? "Documento"}
          </span>
        </div>
      </div>

      <div className="pac-docx-preview__viewport">
        <article
          className="pac-docx-preview__page"
          dangerouslySetInnerHTML={{ __html: data.html }}
        />
      </div>

      {data.truncated ? (
        <p className="pac-muted pac-docx-preview__truncated">
          Conteúdo truncado na pré-visualização. Baixe o arquivo para ver o documento completo.
        </p>
      ) : null}
    </div>
  );
}
