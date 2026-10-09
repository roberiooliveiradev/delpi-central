import { useEffect, useState } from "react";
import { renderBpmnThumbnail } from "@delpi/bpmn-editor";
import { Expand, Eye, GitBranch, Pencil } from "lucide-react";

import type { AppProps } from "../../App";
import {
  fetchProcessBpmnWorkingCopy,
  type ProcessBpmnDocument,
} from "../../data/api/bpmnDocumentApi";
import { buildProcessoBpmnEditPath } from "../../utils/routeParser";
import { DS_GHOST_BTN } from "../ghostChrome";
import { HostContainedPageDialog, WideModal } from "../ui/Modal";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  document: ProcessBpmnDocument;
  processName?: string;
  onNavigate: (path: string) => void;
};

type PreviewState =
  | { kind: "loading" }
  | { kind: "svg"; svg: string }
  | { kind: "empty" }
  | { kind: "error" };

/**
 * Prévia read-only do BPMN nativo vigente (G9): thumbnail SVG derivado do
 * working copy canônico via renderer compartilhado + lightbox/page dialog.
 * Nenhum write, nenhuma fonte paralela — a única autoridade segue sendo o
 * documento nativo do Transformômetro.
 */
export function ProcessBpmnPreview({
  processoId,
  document,
  processName,
  getAccessToken,
  onNavigate,
}: Props) {
  const [preview, setPreview] = useState<PreviewState>({ kind: "loading" });
  const [lightbox, setLightbox] = useState<"wide" | "page" | null>(null);

  useEffect(() => {
    let cancelled = false;
    setPreview({ kind: "loading" });
    void fetchProcessBpmnWorkingCopy(processoId, getAccessToken)
      .then((wc) => renderBpmnThumbnail(wc.xml))
      .then((result) => {
        if (cancelled) return;
        setPreview(
          result.kind === "svg" ? { kind: "svg", svg: result.svg } : { kind: "empty" },
        );
      })
      .catch(() => {
        if (!cancelled) setPreview({ kind: "error" });
      });
    return () => {
      cancelled = true;
    };
  }, [processoId, document.working_copy_sha256, getAccessToken]);

  const svgMarkup = preview.kind === "svg" ? preview.svg : null;
  const updatedAt = document.updated_at
    ? new Date(document.updated_at).toLocaleString("pt-BR")
    : null;

  return (
    <div className="tm-bpmn-preview" data-testid="bpmn-preview">
      <div className="tm-bpmn-preview__meta">
        <p className="ds-hint" style={{ margin: 0 }}>
          <GitBranch size={14} aria-hidden />{" "}
          {processName ? <strong>{processName} — </strong> : null}
          documento BPMN nativo, working copy{" "}
          <strong>v{document.version}</strong>
          {updatedAt ? ` · atualizado ${updatedAt}` : ""} · sha{" "}
          <code>{document.working_copy_sha256.slice(0, 10)}…</code>
        </p>
      </div>

      {preview.kind === "loading" ? (
        <div className="tm-bpmn-preview__stage tm-bpmn-preview__stage--loading">
          <p className="ds-hint">Gerando prévia do diagrama…</p>
        </div>
      ) : svgMarkup ? (
        <button
          type="button"
          className="tm-bpmn-preview__stage"
          aria-label="Ampliar prévia do diagrama"
          title="Clique para ampliar"
          onClick={() => setLightbox("wide")}
          dangerouslySetInnerHTML={{ __html: svgMarkup }}
        />
      ) : (
        <div className="tm-bpmn-preview__stage tm-bpmn-preview__stage--empty">
          <p className="ds-hint">
            {preview.kind === "empty"
              ? "O diagrama ainda não tem elementos para pré-visualizar."
              : "Não foi possível renderizar a prévia — abra o editor para ver o diagrama."}
          </p>
        </div>
      )}

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
        <button
          type="button"
          className={DS_GHOST_BTN}
          disabled={!svgMarkup}
          onClick={() => setLightbox("wide")}
        >
          <Eye size={14} aria-hidden /> Ver prévia
        </button>
        <button
          type="button"
          className={DS_GHOST_BTN}
          disabled={!svgMarkup}
          onClick={() => setLightbox("page")}
        >
          <Expand size={14} aria-hidden /> Tela cheia
        </button>
        <button
          type="button"
          className={DS_GHOST_BTN}
          onClick={() => onNavigate(buildProcessoBpmnEditPath(processoId))}
        >
          <Pencil size={14} aria-hidden /> Editar diagrama
        </button>
      </div>

      {lightbox === "wide" ? (
        <WideModal
          open
          title="Prévia do diagrama BPMN"
          onClose={() => setLightbox(null)}
        >
          <div
            className="tm-bpmn-preview__lightbox"
            dangerouslySetInnerHTML={{ __html: svgMarkup ?? "" }}
          />
          <p className="ds-hint">Visualização somente leitura.</p>
        </WideModal>
      ) : null}
      {lightbox === "page" ? (
        <HostContainedPageDialog
          open
          title="Prévia do diagrama BPMN"
          onClose={() => setLightbox(null)}
        >
          <div
            className="tm-bpmn-preview__lightbox tm-bpmn-preview__lightbox--full"
            dangerouslySetInnerHTML={{ __html: svgMarkup ?? "" }}
          />
          <p className="ds-hint">Visualização somente leitura.</p>
        </HostContainedPageDialog>
      ) : null}
    </div>
  );
}
