import { useEffect, useState } from "react";

import type { SchedulingResource } from "../api/schedulingApi";
import { RESOURCE_TYPES, type BranchCode, type ResourceType } from "../constants/scheduling";

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
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setName(resource?.name ?? "");
    setResourceType(resource?.resource_type ?? "meeting_room");
    setDescription(resource?.description ?? "");
    setCapacity(resource?.capacity ? String(resource.capacity) : "");
    setPlate(String(resource?.metadata?.plate ?? ""));
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
          <label className="ca-field">
            <span>Nome</span>
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Ex.: Sala Azul"
              required
            />
          </label>

          <label className="ca-field">
            <span>Tipo</span>
            <select
              value={resourceType}
              onChange={(event) => setResourceType(event.target.value as ResourceType)}
            >
              {RESOURCE_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </label>

          <label className="ca-field">
            <span>Descrição</span>
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={3}
              placeholder="Localização, equipamentos, observações..."
            />
          </label>

          <div className="ca-form-row">
            <label className="ca-field">
              <span>Capacidade</span>
              <input
                type="number"
                min={1}
                value={capacity}
                onChange={(event) => setCapacity(event.target.value)}
                placeholder="Opcional"
              />
            </label>

            {resourceType === "company_car" ? (
              <label className="ca-field">
                <span>Placa</span>
                <input
                  value={plate}
                  onChange={(event) => setPlate(event.target.value)}
                  placeholder="ABC1D23"
                />
              </label>
            ) : null}
          </div>

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
