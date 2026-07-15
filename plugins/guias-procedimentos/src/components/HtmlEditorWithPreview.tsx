import { useState } from "react";

import { SanitizedArticleContent } from "./SanitizedArticleContent";

type HtmlEditorWithPreviewProps = {
  value: string;
  onChange: (next: string) => void;
  disabled?: boolean;
  id?: string;
};

type Pane = "html" | "preview" | "split";

const HELP =
  "Tags aceitas: h2–h5, p, br, strong, em, ul/ol/li, blockquote, table, a, figure/img/video controlados (guide-media), anexos (guide-attachment), div/span com gp-callout e gp-emphasis. Scripts, iframes e estilos inline são removidos na prévia e na API. Prefira inserir mídias pela aba Mídias/Anexos.";

function initialPane(): Pane {
  if (typeof window === "undefined") return "split";
  if (window.matchMedia("(max-width: 768px)").matches) return "html";
  return "split";
}

export function HtmlEditorWithPreview({
  value,
  onChange,
  disabled = false,
  id = "content-html",
}: HtmlEditorWithPreviewProps) {
  const [pane, setPane] = useState<Pane>(initialPane);

  return (
    <div className="gp-html-editor">
      <div className="gp-html-editor__toolbar">
        <div className="gp-html-editor__tabs" role="tablist">
          {(
            [
              ["html", "HTML"],
              ["preview", "Prévia"],
              ["split", "Dividido"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={pane === key}
              className={`gp-btn gp-btn--ghost gp-btn--compact${
                pane === key ? " is-active" : ""
              }`}
              onClick={() => setPane(key)}
            >
              {label}
            </button>
          ))}
        </div>
        <span className="gp-html-editor__count">
          {value.length.toLocaleString("pt-BR")} caracteres
        </span>
      </div>
      <p className="gp-html-editor__help">{HELP}</p>
      <div
        className={`gp-html-editor__panes gp-html-editor__panes--${pane}`}
      >
        {pane !== "preview" ? (
          <label className="gp-field gp-html-editor__code">
            <span className="gp-visually-hidden">HTML do artigo</span>
            <textarea
              id={id}
              className="gp-textarea gp-textarea--code"
              value={value}
              disabled={disabled}
              spellCheck={false}
              rows={18}
              onChange={(event) => onChange(event.target.value)}
            />
          </label>
        ) : null}
        {pane !== "html" ? (
          <div className="gp-html-editor__preview" aria-live="polite">
            <p className="gp-html-editor__preview-label">Prévia segura</p>
            <SanitizedArticleContent html={value} />
          </div>
        ) : null}
      </div>
    </div>
  );
}
