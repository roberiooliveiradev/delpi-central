import type {
  AdminToolHealthItem,
  AdminToolsBackendPlaceholders,
} from "./toolsTypes";

import "./ToolHealthPanel.css";

const DEFAULT_HEALTH_ITEMS: AdminToolHealthItem[] = [
  {
    id: "llm-provider",
    label: "Provider LLM",
    status: "unknown",
    description: "Aguardando healthcheck detalhado do backend.",
  },
  {
    id: "embedding",
    label: "Embeddings",
    status: "unknown",
    description: "Aguardando status de indexação e vetorizações.",
  },
  {
    id: "external-actions",
    label: "External actions",
    status: "unknown",
    description: "Aguardando status dos providers OpenAPI.",
  },
];

type ToolHealthPanelProps = Pick<AdminToolsBackendPlaceholders, "loadToolHealth"> & {
  items?: AdminToolHealthItem[];
};

const STATUS_LABEL: Record<AdminToolHealthItem["status"], string> = {
  ok: "OK",
  warning: "Atenção",
  error: "Erro",
  unknown: "Pendente",
};

export function ToolHealthPanel({
  items = DEFAULT_HEALTH_ITEMS,
  loadToolHealth,
}: ToolHealthPanelProps) {
  return (
    <article className="mdc-tool-health-panel">
      <div className="mdc-tool-health-panel__header">
        <div>
          <p className="mdc-chat-eyebrow">Saúde operacional</p>
          <h2>Status técnico</h2>
        </div>

        <button
          type="button"
          disabled={!loadToolHealth}
          title={loadToolHealth ? "Recarregar status" : "Aguardando endpoint de health"}
          onClick={() => {
            void loadToolHealth?.();
          }}
        >
          Verificar
        </button>
      </div>

      <div className="mdc-tool-health-panel__list">
        {items.map((item) => (
          <div key={item.id} className="mdc-tool-health-panel__item">
            <div>
              <strong>{item.label}</strong>
              <p>{item.description}</p>
            </div>

            <span className={`is-${item.status}`}>{STATUS_LABEL[item.status]}</span>
          </div>
        ))}
      </div>
    </article>
  );
}
