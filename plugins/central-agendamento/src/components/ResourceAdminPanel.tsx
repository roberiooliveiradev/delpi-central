import { Pencil, Plus, Power } from "lucide-react";

import type { SchedulingResource } from "../api/schedulingApi";
import { RESOURCE_TYPES, resourceTypeLabel } from "../constants/scheduling";

type Props = {
  resources: SchedulingResource[];
  onCreate: () => void;
  onEdit: (resource: SchedulingResource) => void;
  onToggleActive: (resource: SchedulingResource) => Promise<void>;
};

export function ResourceAdminPanel({
  resources,
  onCreate,
  onEdit,
  onToggleActive,
}: Props) {
  return (
    <section className="ca-admin-panel">
      <div className="ca-admin-panel__head">
        <div>
          <h2>Gerenciar recursos</h2>
          <p className="ca-muted">
            Cadastre salas, salas de treinamento, veículos e demais recursos agendáveis.
          </p>
        </div>
        <button type="button" className="ca-btn ca-btn--primary" onClick={onCreate}>
          <Plus size={16} />
          Novo recurso
        </button>
      </div>

      {resources.length === 0 ? (
        <div className="ca-empty-state">
          <p>Nenhum recurso cadastrado ainda.</p>
          <button type="button" className="ca-btn ca-btn--ghost" onClick={onCreate}>
            Cadastrar primeiro recurso
          </button>
        </div>
      ) : (
        <div className="ca-table-wrap">
          <table className="ca-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Tipo</th>
                <th>Capacidade</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {resources.map((resource) => (
                <tr key={resource.id}>
                  <td data-label="Nome">
                    <strong>{resource.name}</strong>
                    {resource.description ? (
                      <small className="ca-table__sub">{resource.description}</small>
                    ) : null}
                  </td>
                  <td data-label="Tipo">{resourceTypeLabel(resource.resource_type)}</td>
                  <td data-label="Capacidade">{resource.capacity ?? "—"}</td>
                  <td data-label="Status">
                    <span
                      className={`ca-badge ${resource.active ? "ca-badge--success" : "ca-badge--muted"}`}
                    >
                      {resource.active ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                  <td data-label="Ações">
                    <div className="ca-table__actions">
                      <button
                        type="button"
                        className="ca-icon-btn"
                        aria-label={`Editar ${resource.name}`}
                        onClick={() => onEdit(resource)}
                      >
                        <Pencil size={16} />
                      </button>
                      <button
                        type="button"
                        className="ca-icon-btn"
                        aria-label={resource.active ? "Desativar" : "Ativar"}
                        onClick={() => void onToggleActive(resource)}
                      >
                        <Power size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="ca-muted ca-admin-panel__hint">
        Tipos disponíveis: {RESOURCE_TYPES.map((item) => item.label).join(" · ")}
      </p>
    </section>
  );
}
