import type {
  AdminExternalActionSummary,
  AdminToolsBackendPlaceholders,
} from "./toolsTypes";

import "./ExternalActionsPanel.css";

const DEFAULT_ACTIONS: AdminExternalActionSummary[] = [
  {
    id: "openapi-providers",
    name: "Providers OpenAPI",
    provider: "Minha DELPI",
    status: "unknown",
    lastRunLabel: "Aguardando endpoint",
    calls24h: 0,
  },
  {
    id: "agent-actions",
    name: "Actions por agente",
    provider: "Agentes",
    status: "unknown",
    lastRunLabel: "Aguardando endpoint",
    calls24h: 0,
  },
  {
    id: "tool-permissions",
    name: "Permissões de tools",
    provider: "RBAC",
    status: "unknown",
    lastRunLabel: "Aguardando endpoint",
    calls24h: 0,
  },
];

type ExternalActionsPanelProps = Pick<
  AdminToolsBackendPlaceholders,
  "loadExternalActions" | "testExternalAction" | "syncOpenApiProviders"
> & {
  actions?: AdminExternalActionSummary[];
};

const STATUS_LABEL: Record<AdminExternalActionSummary["status"], string> = {
  ok: "OK",
  warning: "Atenção",
  error: "Erro",
  unknown: "Pendente",
};

export function ExternalActionsPanel({
  actions = DEFAULT_ACTIONS,
  loadExternalActions,
  testExternalAction,
  syncOpenApiProviders,
}: ExternalActionsPanelProps) {
  return (
    <article className="mdc-external-actions-panel">
      <div className="mdc-external-actions-panel__header">
        <div>
          <p className="mdc-chat-eyebrow">Actions</p>
          <h2>Ferramentas e actions</h2>
        </div>

        <button
          type="button"
          disabled={!syncOpenApiProviders}
          title={syncOpenApiProviders ? "Sincronizar providers" : "Aguardando endpoint de sincronização"}
          onClick={() => {
            void syncOpenApiProviders?.();
          }}
        >
          Sincronizar
        </button>
      </div>

      <p className="mdc-chat-muted">
        Painel preparado para providers OpenAPI, actions por agente, permissões e uso nas últimas 24h.
      </p>

      <div className="mdc-external-actions-panel__list">
        {actions.map((action) => (
          <article key={action.id} className="mdc-external-actions-panel__item">
            <div>
              <strong>{action.name}</strong>
              <p>
                {action.provider} · {action.calls24h} chamada(s) em 24h · {action.lastRunLabel}
              </p>
            </div>

            <div className="mdc-external-actions-panel__actions">
              <span className={`is-${action.status}`}>{STATUS_LABEL[action.status]}</span>

              <button
                type="button"
                disabled={!testExternalAction}
                title={testExternalAction ? "Testar action" : "Aguardando endpoint de teste"}
                onClick={() => {
                  void testExternalAction?.(action.id);
                }}
              >
                Testar
              </button>
            </div>
          </article>
        ))}
      </div>

      <button
        type="button"
        disabled={!loadExternalActions}
        title={loadExternalActions ? "Recarregar actions" : "Aguardando endpoint de listagem"}
        onClick={() => {
          void loadExternalActions?.();
        }}
      >
        Recarregar catálogo
      </button>
    </article>
  );
}
