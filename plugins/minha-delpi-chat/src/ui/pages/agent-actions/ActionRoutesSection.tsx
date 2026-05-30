import { DatabaseZap, Route } from "lucide-react";

import type {
  ChatActionCatalogItem,
  ChatActionProvider,
  ChatActionTestLog,
  ChatActionTestResult,
  ChatAgentActionProvider,
} from "../../../data/api/chatTypes";
import { AgentBuilderCheckbox } from "../../components/agent-builder/AgentBuilderCheckbox";
import { ActionTestPanel } from "./ActionTestPanel";
import type { ActionTestPayload } from "./types";

import "./ActionRoutesSection.css";

type ActionRoutesSectionProps = {
  selectedProvider: ChatActionProvider | null;
  selectedLink: ChatAgentActionProvider | null;
  providerActions: ChatActionCatalogItem[];
  isLoadingRoutes: boolean;
  testingActionId: string | null;
  testAction: ChatActionCatalogItem | null;
  testResult: ChatActionTestResult | null;
  testLogs: ChatActionTestLog[];
  isActionEnabled: (action: ChatActionCatalogItem) => boolean;
  onToggleAction: (action: ChatActionCatalogItem, enabled: boolean) => void;
  onOpenTestPanel: (action: ChatActionCatalogItem) => void;
  onRunActionTest: (payload: ActionTestPayload) => Promise<void>;
  onCloseTestPanel: () => void;
  onUpdateProviderPermissions: (
    patch: Partial<
      Pick<
        ChatAgentActionProvider,
        "allowRead" | "allowWrite" | "allowAdmin" | "requiresConfirmationForWrite"
      >
    >,
  ) => void;
};

export function ActionRoutesSection({
  selectedProvider,
  selectedLink,
  providerActions,
  isLoadingRoutes,
  testingActionId,
  testAction,
  testResult,
  testLogs,
  isActionEnabled,
  onToggleAction,
  onOpenTestPanel,
  onRunActionTest,
  onCloseTestPanel,
  onUpdateProviderPermissions,
}: ActionRoutesSectionProps) {
  return (
    <section className="mdc-chat-agent-actions-page__section">
      <div className="mdc-chat-agent-actions-page__section-title">
        <Route size={18} aria-hidden="true" />
        <div>
          <h2>Ações disponíveis</h2>
          <p>
            {selectedProvider
              ? `${selectedProvider.name} · ${providerActions.length} rota(s)`
              : "Action não encontrada"}
          </p>
        </div>
      </div>

      {selectedLink ? (
        <div className="mdc-chat-agent-actions-page__permissions">
          <AgentBuilderCheckbox
            checked={selectedLink.allowRead}
            onChange={(event) =>
              onUpdateProviderPermissions({ allowRead: event.target.checked })
            }
            label="Leitura"
          />
          <AgentBuilderCheckbox
            checked={selectedLink.allowWrite}
            onChange={(event) =>
              onUpdateProviderPermissions({ allowWrite: event.target.checked })
            }
            label="Escrita"
          />
          <AgentBuilderCheckbox
            checked={selectedLink.allowAdmin}
            onChange={(event) =>
              onUpdateProviderPermissions({ allowAdmin: event.target.checked })
            }
            label="Admin"
          />
          <AgentBuilderCheckbox
            checked={selectedLink.requiresConfirmationForWrite}
            onChange={(event) =>
              onUpdateProviderPermissions({
                requiresConfirmationForWrite: event.target.checked,
              })
            }
            label="Confirmar escrita"
          />
        </div>
      ) : null}

      {isLoadingRoutes ? (
        <p className="mdc-chat-muted">Carregando rotas...</p>
      ) : providerActions.length > 0 ? (
        <div className="mdc-action-routes-table">
          <div className="mdc-action-routes-table__header">
            <span>Nome</span>
            <span>Método</span>
            <span>Caminho</span>
            <span>Status</span>
            <span>Teste</span>
          </div>

          {providerActions.map((action) => (
            <div className="mdc-action-routes-table__group" key={action.actionId}>
              <article className="mdc-action-routes-table__row">
                <label>
                  <input
                    type="checkbox"
                    checked={isActionEnabled(action)}
                    onChange={(event) => onToggleAction(action, event.target.checked)}
                  />
                  <span>{action.operationId || action.actionId}</span>
                </label>

                <span>{action.method ?? "-"}</span>
                <span>{action.path ?? "-"}</span>
                <small>{action.sensitivity || "read"}</small>

                <button
                  type="button"
                  onClick={() => onOpenTestPanel(action)}
                  disabled={testingActionId === action.actionId}
                >
                  {testingActionId === action.actionId ? "Testando..." : "Testar"}
                </button>
              </article>

              {testAction?.actionId === action.actionId ? (
                <ActionTestPanel
                  action={testAction}
                  isRunning={testingActionId === testAction.actionId}
                  result={testResult}
                  logs={testLogs}
                  onRun={onRunActionTest}
                  onClose={onCloseTestPanel}
                />
              ) : null}
            </div>
          ))}
        </div>
      ) : (
        <div className="mdc-chat-agent-actions-page__empty">
          <DatabaseZap size={24} aria-hidden="true" />
          <strong>Nenhuma rota importada</strong>
          <p>Use “Atualizar rotas” para importar as rotas desta action.</p>
        </div>
      )}
    </section>
  );
}
