import { useEffect, useRef, useState } from "react";
import {
  FilePlus2,
  FileUp,
  GitBranch,
  Pencil,
  Sparkles,
  Trash2,
} from "lucide-react";

import type { AppProps } from "../../App";
import {
  createProcessBpmnDocument,
  deleteProcessBpmnDocument,
  fetchProcessBpmnDocument,
  type ProcessBpmnDocument,
} from "../../data/api/bpmnDocumentApi";
import { fetchProcessBpmnReference } from "../../data/api/bpmnReferenceApi";
import { fetchProcessoDiagramaComposed } from "../../data/api/transformometroDiagramApi";
import { buildProcessoBpmnEditPath } from "../../utils/routeParser";
import { ConfirmModal } from "../ui/ConfirmModal";
import { DS_GHOST_BTN } from "../ghostChrome";
import { BpmnMigrationWizard } from "./BpmnMigrationWizard";
import { ProcessBpmnReferenceCard } from "./ProcessBpmnReferenceCard";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  onNavigate: (path: string) => void;
  onError?: (message: string | null) => void;
  /** Estado nativo carregado — a página reconcilia a seção legada (G8H). */
  onDocumentChange?: (document: ProcessBpmnDocument | null) => void;
};

function describeError(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback;
}

/**
 * Card dual-mode do BPMN do processo (G7 / ADR-006):
 *  - documento nativo ativo → editar/histórico/excluir;
 *  - sem nativo → referência externa (G5) OU criar/importar nativo (XOR
 *    garantido no backend; a UI só oferece o que o estado permite).
 */
export function ProcessBpmnCard({
  processoId,
  getAccessToken,
  onNavigate,
  onError,
  onDocumentChange,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [document, setDocument] = useState<ProcessBpmnDocument | null>(null);
  const [hasExternalRef, setHasExternalRef] = useState(false);
  const [refLoaded, setRefLoaded] = useState(false);
  const [hasLegacy, setHasLegacy] = useState(false);
  const [migrationOpen, setMigrationOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let cancelled = false;
    void Promise.resolve().then(async () => {
      try {
        const [docPayload, refPayload, composedPayload] = await Promise.all([
          fetchProcessBpmnDocument(processoId, getAccessToken),
          fetchProcessBpmnReference(processoId, getAccessToken).catch(
            () => null,
          ),
          fetchProcessoDiagramaComposed(processoId, getAccessToken).catch(
            () => null,
          ),
        ]);
        if (cancelled) return;
        setDocument(docPayload?.document ?? null);
        onDocumentChange?.(docPayload?.document ?? null);
        setHasExternalRef(refPayload?.reference != null);
        setRefLoaded(true);
        setHasLegacy(
          (composedPayload?.flowchart?.nodes ?? []).length > 0,
        );
      } catch (err) {
        if (cancelled) return;
        const message = describeError(
          err,
          "Falha ao carregar o BPMN do processo.",
        );
        setLocalError(message);
        onError?.(message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [processoId, getAccessToken, onError, onDocumentChange]);

  async function handleCreate(xml: string | null) {
    setBusy(true);
    setLocalError(null);
    try {
      await createProcessBpmnDocument(processoId, xml, getAccessToken);
      onNavigate(buildProcessoBpmnEditPath(processoId));
    } catch (err) {
      setLocalError(describeError(err, "Falha ao criar o documento BPMN."));
    } finally {
      setBusy(false);
    }
  }

  async function handleImportFile(file: File) {
    const xml = await file.text();
    await handleCreate(xml);
  }

  async function handleDelete() {
    setBusy(true);
    try {
      await deleteProcessBpmnDocument(processoId, getAccessToken);
      setDeleteOpen(false);
      setDocument(null);
    } catch (err) {
      setLocalError(
        describeError(err, "Falha ao remover o documento BPMN."),
      );
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return <p className="ds-hint">Carregando BPMN do processo…</p>;
  }

  return (
    <div className="tm-bpmn-card" data-testid="bpmn-card">
      {localError ? <p className="ds-hint">{localError}</p> : null}

      {document ? (
        <div>
          <p className="ds-hint">
            <GitBranch size={14} aria-hidden /> Documento BPMN nativo — working
            copy <strong>v{document.version}</strong>. Edições são governadas
            com salvamento automático e revisões explícitas.
          </p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button
              type="button"
              className={DS_GHOST_BTN}
              onClick={() => onNavigate(buildProcessoBpmnEditPath(processoId))}
            >
              <Pencil size={14} aria-hidden /> Editar diagrama
            </button>
            <button
              type="button"
              className={DS_GHOST_BTN}
              disabled={busy}
              onClick={() => setDeleteOpen(true)}
            >
              <Trash2 size={14} aria-hidden /> Remover documento
            </button>
          </div>
        </div>
      ) : (
        <div>
          {refLoaded && !hasExternalRef ? (
            <div style={{ marginBottom: 12 }}>
              <p className="ds-hint">
                Crie o diagrama BPMN nativo deste processo — editável aqui
                mesmo, com histórico de revisões — ou vincule um modelo
                externo do Modelador abaixo.
                {hasLegacy
                  ? " Este processo possui um mapeamento legado que pode ser migrado pelo TÉO."
                  : ""}
              </p>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {hasLegacy ? (
                  <button
                    type="button"
                    className={DS_GHOST_BTN}
                    onClick={() => setMigrationOpen(true)}
                  >
                    <Sparkles size={14} aria-hidden /> Migrar para BPMN com
                    TÉO
                  </button>
                ) : null}
                <button
                  type="button"
                  className={DS_GHOST_BTN}
                  disabled={busy}
                  onClick={() => void handleCreate(null)}
                >
                  <FilePlus2 size={14} aria-hidden /> Criar diagrama BPMN
                </button>
                <button
                  type="button"
                  className={DS_GHOST_BTN}
                  disabled={busy}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <FileUp size={14} aria-hidden /> Importar arquivo .bpmn
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".bpmn,.xml,application/xml,text/xml"
                  hidden
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    event.target.value = "";
                    if (file) void handleImportFile(file);
                  }}
                />
              </div>
            </div>
          ) : null}
          <ProcessBpmnReferenceCard
            processoId={processoId}
            getAccessToken={getAccessToken}
            onError={onError}
          />
        </div>
      )}

      <BpmnMigrationWizard
        processoId={processoId}
        getAccessToken={getAccessToken}
        open={migrationOpen}
        onClose={() => setMigrationOpen(false)}
        onMigrated={() => {
          setMigrationOpen(false);
          onNavigate(buildProcessoBpmnEditPath(processoId));
        }}
      />

      <ConfirmModal
        open={deleteOpen}
        title="Remover documento BPMN"
        message="O documento nativo e seu histórico de revisões serão removidos deste processo. Esta ação não pode ser desfeita."
        confirmLabel="Remover"
        variant="danger"
        confirmBusy={busy}
        onCancel={() => setDeleteOpen(false)}
        onConfirm={() => void handleDelete()}
      />
    </div>
  );
}
