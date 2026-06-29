import { useEffect, useRef, useState } from "react";
import { Download, Eye, Trash2, Upload } from "lucide-react";

import {
  deletePlanEvidence,
  downloadPlanEvidenceFile,
  fetchPlanEvidenceFileBlob,
  uploadPlanEvidence,
} from "../api/actionPlansApi";
import type { PlanAction } from "../types/actionPlan";
import type { PlanEvidence } from "../types/rnc8d";
import { formatDateTime } from "../utils/format";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import { StateAlert } from "./StateAlert";
import { Modal } from "./ui/Modal";
import { SectionCard } from "./ui/SectionCard";
import { SelectField } from "./ui/SelectField";
import { TextField } from "./ui/TextField";

const EVIDENCE_TYPES = [
  { value: "image", label: "Imagem" },
  { value: "pdf", label: "PDF" },
  { value: "spreadsheet", label: "Planilha" },
  { value: "email", label: "E-mail" },
  { value: "message", label: "Mensagem" },
  { value: "manual_text", label: "Texto" },
  { value: "other", label: "Outro" },
];

const EVIDENCE_SECTIONS = [
  { value: "general", label: "Geral" },
  { value: "nc_description", label: "Descrição NC" },
  { value: "containment", label: "Contenção" },
  { value: "root_cause", label: "Causa raiz" },
  { value: "corrective", label: "Ação corretiva" },
  { value: "effectiveness", label: "Eficácia" },
  { value: "preventive", label: "Preventiva" },
  { value: "documentation", label: "Documentação" },
  { value: "attachments", label: "Anexos (aba evidências)" },
];

type Props = {
  planId: string;
  evidences: PlanEvidence[];
  actions?: PlanAction[];
  onChanged: () => void | Promise<void>;
  title?: string;
  subtitle?: string;
};

function actionLabel(action: PlanAction): string {
  const prefix = action.action_type.replace(/_/g, " ");
  const text = action.description.trim();
  const snippet = text.length > 48 ? `${text.slice(0, 48)}…` : text;
  return `${prefix}: ${snippet}`;
}

function formatSize(bytes?: number | null): string {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

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

export function EvidencePanel({
  planId,
  evidences,
  actions = [],
  onChanged,
  title = "Banco de conhecimento e evidências",
  subtitle = "Anexe prints, PDFs, planilhas e documentos do processo. Visível para o analista e para o agente GPT.",
}: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [evidenceType, setEvidenceType] = useState("image");
  const [section, setSection] = useState("general");
  const [actionId, setActionId] = useState("");
  const [description, setDescription] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewEvidence, setPreviewEvidence] = useState<PlanEvidence | null>(null);

  async function handleUpload(file: File) {
    setUploading(true);
    setError(null);
    try {
      await uploadPlanEvidence(planId, file, {
        evidenceType,
        section,
        actionId: actionId || undefined,
        description: description.trim() || undefined,
        knowledgeVisible: true,
      });
      setDescription("");
      if (fileInputRef.current) fileInputRef.current.value = "";
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao enviar arquivo.");
    } finally {
      setUploading(false);
    }
  }

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

  const actionOptions = [
    { value: "", label: "Nenhuma (plano geral)" },
    ...actions.map((action) => ({ value: action.id, label: actionLabel(action) })),
  ];
  const actionById = new Map(actions.map((action) => [action.id, action]));

  return (
    <SectionCard
      title={title}
      hint={PAC_HELP_TOOLTIPS.sections.evidences}
      subtitle={subtitle}
    >
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}

      <div className="pac-form-grid pac-evidence-upload">
        <SelectField
          id="pac-evidence-type"
          label="Tipo"
          hint={PAC_HELP_TOOLTIPS.evidence.type}
          options={EVIDENCE_TYPES}
          value={evidenceType}
          onChange={setEvidenceType}
          searchable={false}
        />
        <SelectField
          id="pac-evidence-section"
          label="Seção 8D"
          hint={PAC_HELP_TOOLTIPS.evidence.section}
          options={EVIDENCE_SECTIONS}
          value={section}
          onChange={setSection}
          searchable={false}
        />
        {actions.length ? (
          <SelectField
            id="pac-evidence-action"
            label="Vincular à ação"
            hint={PAC_HELP_TOOLTIPS.evidence.linkedAction}
            options={actionOptions}
            value={actionId}
            onChange={setActionId}
            searchable={actions.length > 6}
          />
        ) : null}
        <TextField
          id="pac-evidence-desc"
          label="Descrição"
          hint={PAC_HELP_TOOLTIPS.evidence.description}
          value={description}
          onChange={setDescription}
          fullWidth
        />
        <div className="pac-evidence-upload__footer pac-field--full">
          <input
            ref={fileInputRef}
            type="file"
            className="pac-evidence-upload__input"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) void handleUpload(file);
            }}
          />
          <button
            type="button"
            className="pac-primary-btn pac-evidence-upload__btn"
            disabled={uploading}
            title={PAC_HELP_TOOLTIPS.evidence.upload}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload size={16} aria-hidden="true" />
            <span>{uploading ? "Enviando…" : "Anexar arquivo"}</span>
          </button>
        </div>
      </div>

      {evidences.length ? (
        <div className="pac-table-wrap">
          <table className="pac-table">
            <thead>
              <tr>
                <th>Arquivo</th>
                <th>Tipo</th>
                <th>Seção</th>
                <th>Ação</th>
                <th>Tamanho</th>
                <th>Enviado em</th>
                <th />
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
                  <td>{evidence.type}</td>
                  <td>{evidence.section ?? "general"}</td>
                  <td>
                    {evidence.action_id
                      ? actionById.get(evidence.action_id)?.description ?? evidence.action_id.slice(0, 8)
                      : "—"}
                  </td>
                  <td>{formatSize(evidence.size_bytes)}</td>
                  <td>{formatDateTime(evidence.created_at)}</td>
                  <td className="pac-table-actions">
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
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="pac-muted">Nenhuma evidência anexada ainda.</p>
      )}

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
              <span>{previewEvidence.type}</span>
              <span>{formatSize(previewEvidence.size_bytes)}</span>
              <span>{formatDateTime(previewEvidence.created_at)}</span>
            </div>
          </div>
        ) : null}
      </Modal>
    </SectionCard>
  );
}
