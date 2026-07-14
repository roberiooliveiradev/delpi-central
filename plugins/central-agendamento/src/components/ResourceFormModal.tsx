import { useEffect, useState } from "react";

import type { SchedulingResource } from "../api/schedulingApi";
import { RESOURCE_TYPES, type BranchCode, type ResourceType } from "../constants/scheduling";
import {
  CaNativeSelectField,
  CaNativeTextAreaField,
  CaNativeTextField,
} from "./caFormFields";

type Props = {
  open: boolean;
  branch: BranchCode;
  resource?: SchedulingResource | null;
  loading?: boolean;
  onClose: () => void;
  onSubmit: (payload: {
    name: string;
    resource_type: ResourceType;
    description?: string;
    capacity?: number;
    metadata?: Record<string, unknown>;
    requires_approval?: boolean;
  }) => Promise<void>;
};

export function ResourceFormModal({
  open,
  branch,
  resource,
  loading = false,
  onClose,
  onSubmit,
}: Props) {
  const [name, setName] = useState("");
  const [resourceType, setResourceType] = useState<ResourceType>("meeting_room");
  const [description, setDescription] = useState("");
  const [capacity, setCapacity] = useState("");
  const [plate, setPlate] = useState("");
  const [requiresApproval, setRequiresApproval] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setName(resource?.name ?? "");
    setResourceType(resource?.resource_type ?? "meeting_room");
    setDescription(resource?.description ?? "");
    setCapacity(resource?.capacity ? String(resource.capacity) : "");
    setPlate(String(resource?.metadata?.plate ?? ""));
    setRequiresApproval(Boolean(resource?.requires_approval));
    setError(null);
  }, [open, resource]);

  if (!open) return null;

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError("Informe o nome do recurso.");
      return;
    }

    const metadata: Record<string, unknown> = {};
    if (resourceType === "company_car" && plate.trim()) {
      metadata.plate = plate.trim().toUpperCase();
    }

    try {
      await onSubmit({
        name: name.trim(),
        resource_type: resourceType,
        description: description.trim() || undefined,
        capacity: capacity ? Number(capacity) : undefined,
        metadata: Object.keys(metadata).length > 0 ? metadata : undefined,
        requires_approval: requiresApproval,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar recurso.");
    }
  }

  return (
    <div className="ca-modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="ca-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ca-resource-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="ca-modal__header">
          <div>
            <p className="ca-modal__eyebrow">{branch}</p>
            <h2 id="ca-resource-title">
              {resource ? "Editar recurso" : "Novo recurso"}
            </h2>
          </div>
          <button type="button" className="ca-icon-btn" onClick={onClose} aria-label="Fechar">
            ×
          </button>
        </div>

        <form className="ca-form" onSubmit={(event) => void handleSubmit(event)}>
          <CaNativeTextField
            id="ca-resource-name"
            label="Nome"
            value={name}
            onChange={setName}
            placeholder="Ex.: Sala Azul"
            required
          />

          <CaNativeSelectField
            id="ca-resource-type"
            label="Tipo"
            value={resourceType}
            onChange={(value) => setResourceType(value as ResourceType)}
            options={RESOURCE_TYPES.map((type) => ({
              value: type.value,
              label: type.label,
            }))}
          />

          <CaNativeTextAreaField
            id="ca-resource-description"
            label="Descrição"
            value={description}
            onChange={setDescription}
            rows={3}
            span={false}
            placeholder="Localização, equipamentos, observações..."
          />

          <div className="ca-form-row">
            <CaNativeTextField
              id="ca-resource-capacity"
              label="Capacidade"
              type="number"
              min={1}
              value={capacity}
              onChange={setCapacity}
              placeholder="Opcional"
            />

            {resourceType === "company_car" ? (
              <CaNativeTextField
                id="ca-resource-plate"
                label="Placa"
                value={plate}
                onChange={setPlate}
                placeholder="ABC1D23"
              />
            ) : null}
          </div>

          <label className="ca-checkbox">
            <input
              type="checkbox"
              checked={requiresApproval}
              onChange={(event) => setRequiresApproval(event.target.checked)}
            />
            <span>
              Exige aprovação prévia
              <small>Reservas ficam pendentes até um aprovador confirmar.</small>
            </span>
          </label>

          {error ? <p className="ca-alert ca-alert--error">{error}</p> : null}

          <div className="ca-modal__actions">
            <button type="button" className="ca-btn ca-btn--ghost" onClick={onClose}>
              Cancelar
            </button>
            <button type="submit" className="ca-btn ca-btn--primary" disabled={loading}>
              {loading ? "Salvando..." : "Salvar recurso"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
