import { useEffect, useRef, useState } from "react";
import { Download, Eye, Trash2 } from "lucide-react";

import {
  deletePlanEvidence,
  downloadPlanEvidenceFile,
  fetchPlanEvidenceFileBlob,
} from "../../api/actionPlansApi";
import {
  evidenceSectionLabel,
  evidenceTypeLabel,
} from "../../constants/evidence";
import { PAC_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { PlanAction } from "../../types/actionPlan";
import type { PlanEvidence } from "../../types/rnc8d";
import { formatDateTime } from "../../utils/format";
import { Modal } from "../ui/Modal";
import { TableHeaderCell } from "../ui/HelpTooltip";
import {
  formatEvidenceFileSize,
  linkedActionCell,
} from "./evidenceAttachmentUtils";

const T = PAC_HELP_TOOLTIPS.tables;

type Props = {
  planId: string;
  evidences: PlanEvidence[];
  actions?: PlanAction[];
  readOnly?: boolean;
  onChanged: () => void | Promise<void>;
  compact?: boolean;
};

function isImageEvidence(evidence: PlanEvidence): boolean {
  return evidence.type === "image" || Boolean(evidence.mime_type?.startsWith("image/"));
}

function isPdfEvidence(evidence: PlanEvidence): boolean {
  return evidence.type === "pdf" || evidence.mime_type === "application/pdf";
}

function isPreviewableEvidence(evidence: PlanEvidence): boolean {
  return isImageEvidence(evidence) || isPdfEvidence(evidence);
}

function evidenceTitle(evidence: PlanEvidence): string {
  return evidence.file_name ?? evidence.description ?? evidence.id;
}

function EvidencePreviewContent({
  planId,
  evidence,
}: {
  planId: string;
  evidence: PlanEvidence;
}) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const objectUrlRef = useRef<string | null>(null);

  useEffect(() => {
    if (!isPreviewableEvidence(evidence)) {
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function loadPreview() {
      setLoading(true);
      setError(null);
      try {
        const blob = await fetchPlanEvidenceFileBlob(planId, evidence.id);
        if (cancelled) return;
        const url = URL.createObjectURL(blob);
        objectUrlRef.current = url;
        setPreviewUrl(url);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Não foi possível carregar a pré-visualização.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadPreview();

    return () => {
      cancelled = true;
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
    };
  }, [planId, evidence.id, evidence.type, evidence.mime_type]);

  const title = evidenceTitle(evidence);

  if (loading) {
    return <p className="pac-muted pac-evidence-preview-modal__status">Carregando pré-visualização…</p>;
  }

  if (error) {
    return <p className="pac-muted pac-evidence-preview-modal__status">{error}</p>;
  }

  if (isImageEvidence(evidence) && previewUrl) {
    return (
      <img
        src={previewUrl}
        alt={title}
        className="pac-evidence-preview-modal__image"
      />
    );
  }

  if (isPdfEvidence(evidence) && previewUrl) {
    return (
      <iframe
        src={previewUrl}
        title={`Pré-visualização: ${title}`}
        className="pac-evidence-preview-modal__pdf"
      />
    );
  }

  return (
    <p className="pac-muted pac-evidence-preview-modal__status">
      Pré-visualização não disponível para este tipo de arquivo.
    </p>
  );
}

export function EvidenceListTable({
  planId,
  evidences,
  actions = [],
  readOnly = false,
  onChanged,
  compact = false,
}: Props) {
  const [error, setError] = useState<string | null>(null);
  const [previewEvidence, setPreviewEvidence] = useState<PlanEvidence | null>(null);
  const actionById = new Map(actions.map((action) => [action.id, action]));

  async function handleDelete(evidenceId: string) {
    setError(null);
    try {
      await deletePlanEvidence(planId, evidenceId);
      if (previewEvidence?.id === evidenceId) {
        setPreviewEvidence(null);
      }
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao remover evidência.");
    }
  }

  if (!evidences.length) {
    return <p className="pac-muted">Nenhuma evidência anexada ainda.</p>;
  }

  return (
    <>
      {error ? <p className="pac-muted pac-evidence-list__error">{error}</p> : null}
      <div className={`pac-table-wrap${compact || readOnly ? " pac-table-wrap--compact-read" : ""}`}>
        <table className={`pac-table${compact || readOnly ? " pac-table--compact-read" : ""}`}>
          <thead>
            <tr>
              <TableHeaderCell label="Arquivo" hint={T.file} />
              <TableHeaderCell label="Tipo" hint={T.evidenceType} />
              <TableHeaderCell label="Seção" hint={T.sectionRef} />
              <TableHeaderCell label="Ação" hint={T.linkedAction} />
              <TableHeaderCell label="Tamanho" hint={T.fileSize} />
              <TableHeaderCell label="Enviado em" hint={T.uploadedAt} />
              {!readOnly ? (
                <TableHeaderCell
                  label="Ações"
                  hint={T.evidenceActions}
                  className="pac-table__actions-col"
                />
              ) : null}
            </tr>
          </thead>
          <tbody>
            {evidences.map((evidence) => (
              <tr key={evidence.id}>
                <td>
                  <div className="pac-evidence-name">
                    <span>{evidence.file_name ?? evidence.id}</span>
                    {evidence.description ? (
                      <small className="pac-muted">{evidence.description}</small>
                    ) : null}
                  </div>
                </td>
                <td>{evidenceTypeLabel(evidence.type)}</td>
                <td>{evidenceSectionLabel(evidence.section)}</td>
                <td className="pac-table-cell--linked-action">
                  {linkedActionCell(evidence.action_id, actionById)}
                </td>
                <td>{formatEvidenceFileSize(evidence.size_bytes)}</td>
                <td>{formatDateTime(evidence.created_at)}</td>
                {!readOnly ? (
                  <td className="pac-table__actions-cell">
                    <div className="pac-table-actions">
                      {isPreviewableEvidence(evidence) ? (
                        <button
                          type="button"
                          className="pac-ghost-btn pac-ghost-btn--icon"
                          aria-label="Pré-visualizar evidência"
                          title="Pré-visualizar"
                          onClick={() => setPreviewEvidence(evidence)}
                        >
                          <Eye size={16} />
                        </button>
                      ) : null}
                      <button
                        type="button"
                        className="pac-ghost-btn pac-ghost-btn--icon"
                        aria-label="Baixar evidência"
                        title="Baixar"
                        onClick={() =>
                          void downloadPlanEvidenceFile(
                            planId,
                            evidence.id,
                            evidence.file_name ?? `evidence-${evidence.id}`,
                          )
                        }
                      >
                        <Download size={16} />
                      </button>
                      <button
                        type="button"
                        className="pac-ghost-btn pac-ghost-btn--icon"
                        aria-label="Remover evidência"
                        title="Remover"
                        onClick={() => void handleDelete(evidence.id)}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Modal
        open={previewEvidence != null}
        title={previewEvidence ? evidenceTitle(previewEvidence) : "Pré-visualização"}
        className="pac-modal--evidence-preview"
        onClose={() => setPreviewEvidence(null)}
      >
        {previewEvidence ? (
          <div className="pac-evidence-preview-modal">
            <EvidencePreviewContent planId={planId} evidence={previewEvidence} />
            {previewEvidence.description ? (
              <p className="pac-muted pac-evidence-preview-modal__description">
                {previewEvidence.description}
              </p>
            ) : null}
            <div className="pac-evidence-preview-modal__meta">
              <span>{evidenceTypeLabel(previewEvidence.type)}</span>
              <span>{formatEvidenceFileSize(previewEvidence.size_bytes)}</span>
              <span>{formatDateTime(previewEvidence.created_at)}</span>
            </div>
          </div>
        ) : null}
      </Modal>
    </>
  );
}
