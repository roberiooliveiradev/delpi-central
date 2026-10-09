import { useEffect, useRef, useState } from "react";
import { BpmnReadonlyViewer } from "@delpi/bpmn-editor";
import type { BpmnReadonlyViewerStatus } from "@delpi/bpmn-editor";
import "@delpi/bpmn-editor/styles.css";
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

type FetchState =
  | { kind: "loading" }
  | { kind: "xml"; xml: string }
  | { kind: "error" };

/**
 * Prévia read-only do BPMN nativo vigente (G9-LAYOUT-1): o próprio
 * NavigatedViewer do renderer compartilhado montado no card — pan, wheel
 * zoom e controles +/−/fit, sem caminho de edição. O mesmo componente é
 * reutilizado no lightbox/tela cheia (muda só o container). Nenhum write,
 * nenhuma fonte paralela — a única autoridade segue sendo o documento
 * nativo do Transformômetro.
 */
export function ProcessBpmnPreview({
  processoId,
  document,
  processName,
  getAccessToken,
  onNavigate,
}: Props) {
  const [fetch, setFetch] = useState<FetchState>({ kind: "loading" });
  const [status, setStatus] = useState<BpmnReadonlyViewerStatus>("loading");
  const [lightbox, setLightbox] = useState<"wide" | "page" | null>(null);
  // retry: bump de reloadKey re-executa o fetch (G9-LOAD-1 §10)
  const [reloadKey, setReloadKey] = useState(0);
  // token vivo por ref — identidade nova não re-dispara o fetch (G9-LOAD-1 §3)
  const tokenRef = useRef(getAccessToken);
  tokenRef.current = getAccessToken;

  useEffect(() => {
    let cancelled = false;
    setFetch({ kind: "loading" });
    setStatus("loading");
    console.debug("[BPMN_LOAD] stage=working-copy surface=preview");
    void fetchProcessBpmnWorkingCopy(processoId, () => tokenRef.current?.())
      .then((wc) => {
        if (!cancelled) setFetch({ kind: "xml", xml: wc.xml });
      })
      .catch((err) => {
        console.debug("[BPMN_LOAD] stage=error surface=preview", {
          errorClass: err instanceof Error ? err.name : typeof err,
          errorMessage: err instanceof Error ? err.message : String(err),
        });
        if (!cancelled) setFetch({ kind: "error" });
      });
    return () => {
      cancelled = true;
    };
  }, [processoId, document.working_copy_sha256, reloadKey]);

  const xml = fetch.kind === "xml" ? fetch.xml : null;
  const viewable = xml != null && status !== "error" && status !== "empty";
  const updatedAt = document.updated_at
    ? new Date(document.updated_at).toLocaleString("pt-BR")
    : null;

  const stageBody = () => {
    if (fetch.kind === "loading" || (xml != null && status === "loading")) {
      return <p className="ds-hint">Carregando prévia do diagrama…</p>;
    }
    if (!xml || status === "error") {
      return (
        <p className="ds-hint">
          Não foi possível renderizar a prévia —{" "}
          <button
            type="button"
            className={DS_GHOST_BTN}
            onClick={() => setReloadKey((k) => k + 1)}
          >
            Tentar novamente
          </button>{" "}
          ou abra o editor para ver o diagrama.
        </p>
      );
    }
    if (status === "empty") {
      return (
        <p className="ds-hint">
          O diagrama ainda não tem elementos para pré-visualizar.
        </p>
      );
    }
    return null;
  };

  return (
    <div className="tm-bpmn-preview" data-testid="bpmn-preview">
      <div className="tm-bpmn-preview__meta">
        <p className="ds-hint" style={{ margin: 0 }}>
          <GitBranch size={14} aria-hidden />{" "}
          {processName ? <strong>{processName} — </strong> : null}
          Working copy <strong>v{document.version}</strong>
          {updatedAt ? ` · atualizado ${updatedAt}` : ""}
          <span
            className="tm-bpmn-preview__sha"
            title={`Checksum do working copy: ${document.working_copy_sha256}`}
          >
            {" "}
            · sha {document.working_copy_sha256.slice(0, 10)}…
          </span>
        </p>
      </div>

      <div
        className={`tm-bpmn-preview__stage${
          viewable ? "" : " tm-bpmn-preview__stage--message"
        }`}
      >
        {xml ? (
          <BpmnReadonlyViewer
            key={reloadKey}
            xml={xml}
            controls
            fitOnLoad
            onStatusChange={setStatus}
            className="tm-bpmn-preview__viewer"
          />
        ) : null}
        {stageBody()}
      </div>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
        <button
          type="button"
          className={DS_GHOST_BTN}
          disabled={!viewable}
          onClick={() => setLightbox("wide")}
        >
          <Eye size={14} aria-hidden /> Ver prévia
        </button>
        <button
          type="button"
          className={DS_GHOST_BTN}
          disabled={!viewable}
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

      {lightbox === "wide" && xml ? (
        <WideModal
          open
          title="Prévia do diagrama BPMN"
          onClose={() => setLightbox(null)}
        >
          <div className="tm-bpmn-preview__lightbox">
            <BpmnReadonlyViewer xml={xml} controls fitOnLoad />
          </div>
          <p className="ds-hint">
            Visualização somente leitura — arraste para navegar, use o scroll
            para zoom.
          </p>
        </WideModal>
      ) : null}
      {lightbox === "page" && xml ? (
        <HostContainedPageDialog
          open
          title="Prévia do diagrama BPMN"
          onClose={() => setLightbox(null)}
        >
          <div className="tm-bpmn-preview__lightbox tm-bpmn-preview__lightbox--full">
            <BpmnReadonlyViewer xml={xml} controls fitOnLoad />
          </div>
          <p className="ds-hint">
            Visualização somente leitura — arraste para navegar, use o scroll
            para zoom.
          </p>
        </HostContainedPageDialog>
      ) : null}
    </div>
  );
}
