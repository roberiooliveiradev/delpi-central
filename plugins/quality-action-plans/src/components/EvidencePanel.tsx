import { useRef, useState } from "react";
import { Download, Trash2, Upload } from "lucide-react";

import {
  deletePlanEvidence,
  downloadPlanEvidenceFile,
  uploadPlanEvidence,
} from "../api/actionPlansApi";
import type { PlanAction } from "../types/actionPlan";
import type { PlanEvidence } from "../types/rnc8d";
import { formatDateTime } from "../utils/format";
import { StateAlert } from "./StateAlert";
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

export function EvidencePanel({ planId, evidences, actions = [], onChanged }: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [evidenceType, setEvidenceType] = useState("image");
  const [section, setSection] = useState("general");
  const [actionId, setActionId] = useState("");
  const [description, setDescription] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      title="Banco de conhecimento e evidências"
      subtitle="Anexe prints, PDFs, planilhas e documentos do processo. Visível para o analista e para o agente GPT."
    >
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}

      <div className="pac-form-grid pac-evidence-upload">
        <SelectField
          id="pac-evidence-type"
          label="Tipo"
          options={EVIDENCE_TYPES}
          value={evidenceType}
          onChange={setEvidenceType}
          searchable={false}
        />
        <SelectField
          id="pac-evidence-section"
          label="Seção 8D"
          options={EVIDENCE_SECTIONS}
          value={section}
          onChange={setSection}
          searchable={false}
        />
        {actions.length ? (
          <SelectField
            id="pac-evidence-action"
            label="Vincular à ação"
            options={actionOptions}
            value={actionId}
            onChange={setActionId}
            searchable={actions.length > 6}
          />
        ) : null}
        <TextField
          id="pac-evidence-desc"
          label="Descrição"
          value={description}
          onChange={setDescription}
          fullWidth
        />
        <div className="pac-evidence-upload__actions">
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
            className="pac-primary-btn"
            disabled={uploading}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload size={16} />
            {uploading ? "Enviando…" : "Anexar arquivo"}
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
                    <button
                      type="button"
                      className="pac-ghost-btn pac-ghost-btn--icon"
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
    </SectionCard>
  );
}
