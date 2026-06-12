import { DatabaseZap, Route, Trash2 } from "lucide-react";

import type {
  ChatActionCatalogItem,
  ChatActionProvider,
  ChatActionTestLog,
  ChatActionTestResult,
  ChatAgentActionProvider,
} from "../../../data/api/chatTypes";
import { AgentBuilderCheckbox } from "../../components/agent-builder/AgentBuilderCheckbox";
import { AgentBuilderSwitch } from "../../components/agent-builder/AgentBuilderSwitch";
import { ActionTestPanel } from "./ActionTestPanel";
import type { ActionTestPayload } from "./types";

import "./ActionRoutesSection.css";

type ActionRoutesSectionProps = {
  selectedProvider: ChatActionProvider | null;
  selectedLink: ChatAgentActionProvider | null;
  providerActions: ChatActionCatalogItem[];
  backgroundImportJob: {
    phaseLabel: string;
    progress: { done: number; total: number };
  } | null;
  isLoadingRoutes: boolean;
  testingActionId: string | null;
  testAction: ChatActionCatalogItem | null;
  testResult: ChatActionTestResult | null;
  testLogs: ChatActionTestLog[];
  isActionEnabled: (action: ChatActionCatalogItem) => boolean;
  hasActionOverride: (action: ChatActionCatalogItem) => boolean;
  onToggleAction: (action: ChatActionCatalogItem, enabled: boolean) => void;
  onRemoveActionOverride: (action: ChatActionCatalogItem) => void;
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
  backgroundImportJob,
  isLoadingRoutes,
  testingActionId,
  testAction,
  testResult,
  testLogs,
  isActionEnabled,
  hasActionOverride,
  onToggleAction,
  onRemoveActionOverride,
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
          {backgroundImportJob ? (
            <p className="mdc-action-routes-section__indexing-badge" role="status">
              {backgroundImportJob.phaseLabel}
              {backgroundImportJob.progress.total > 0
                ? ` — ${backgroundImportJob.progress.done}/${backgroundImportJob.progress.total}`
                : ""}
            </p>
          ) : null}
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
            <span>Ações</span>
          </div>

          {providerActions.map((action) => {
            const enabled = isActionEnabled(action);
            const customized = hasActionOverride(action);

            return (
              <div className="mdc-action-routes-table__group" key={action.actionId}>
                <article className="mdc-action-routes-table__row">
                  <div className="mdc-action-routes-table__name">
                    <AgentBuilderSwitch
                      size="compact"
                      checked={enabled}
                      onChange={(event) => onToggleAction(action, event.target.checked)}
                      ariaLabel={`${enabled ? "Desativar" : "Ativar"} ${action.operationId || action.actionId}`}
                    />
                    <span>{action.operationId || action.actionId}</span>
                  </div>

                  <span>{action.method ?? "-"}</span>
                  <span>{action.path ?? "-"}</span>
                  <span
                    className={[
                      "mdc-action-routes-table__status",
                      enabled
                        ? "mdc-action-routes-table__status--on"
                        : "mdc-action-routes-table__status--off",
                    ].join(" ")}
                  >
                    {enabled ? "Ativa" : "Inativa"}
                    {customized ? " · custom" : ""}
                  </span>

                  <div className="mdc-action-routes-table__actions">
                    <button
                      type="button"
                      className="mdc-chat-ws-outline-btn"
                      onClick={() => onOpenTestPanel(action)}
                      disabled={testingActionId === action.actionId}
                    >
                      {testingActionId === action.actionId ? "Testando..." : "Testar"}
                    </button>
                    {customized ? (
                      <button
                        type="button"
                        className="mdc-action-routes-table__remove"
                        title="Remover personalização"
                        aria-label="Remover personalização da rota"
                        onClick={() => onRemoveActionOverride(action)}
                      >
                        <Trash2 size={15} aria-hidden="true" />
                      </button>
                    ) : null}
                  </div>
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
            );
          })}
        </div>
      ) : (
        <div className="mdc-chat-agent-actions-page__empty">
          <DatabaseZap size={24} aria-hidden="true" />
          <strong>Rota ainda não importada</strong>
          <p>Use “Atualizar rotas” para importar as rotas desta action.</p>
        </div>
      )}
    </section>
  );
}
