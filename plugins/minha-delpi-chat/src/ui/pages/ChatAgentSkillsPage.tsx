import { ArrowLeft, BookOpen, RefreshCw, Sparkles, Zap } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  listChatAgentSkills,
  listChatSkillCatalog,
  upsertChatAgentSkill,
} from "../../data/api/chatApi";
import type { ChatAgent, ChatAgentSkillBinding } from "../../data/api/chatTypes";

import "./ChatAgentSkillsPage.css";

type ChatAgentSkillsPageProps = {
  agent: ChatAgent;
  onBack: () => void;
  onOpenActions?: (agent: ChatAgent) => void;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function ChatAgentSkillsPage({
  agent,
  onBack,
  onOpenActions,
  getAccessToken,
}: ChatAgentSkillsPageProps) {
  const [bindings, setBindings] = useState<ChatAgentSkillBinding[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingKey, setIsSavingKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const enabledCount = useMemo(
    () => bindings.filter((item) => item.enabled).length,
    [bindings],
  );

  const loadSkills = useCallback(async () => {
    if (!getAccessToken) {
      setBindings([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const [catalog, agentSkills] = await Promise.all([
        listChatSkillCatalog({ getAccessToken }),
        listChatAgentSkills(agent.id, { getAccessToken }),
      ]);

      const byKey = new Map(agentSkills.map((item) => [item.skillKey, item]));

      const merged = catalog.map((item) => {
        const current = byKey.get(item.skillKey);

        return (
          current ?? {
            skillKey: item.skillKey,
            label: item.label,
            description: item.description,
            policyFile: item.policyFile,
            enabled: false,
            executionHint: item.executionHint,
            derived: {},
          }
        );
      });

      setBindings(merged);
    } catch {
      setError("Não foi possível carregar as skills deste agente.");
      setBindings([]);
    } finally {
      setIsLoading(false);
    }
  }, [agent.id, getAccessToken]);

  useEffect(() => {
    void loadSkills();
  }, [loadSkills]);

  async function handleToggle(binding: ChatAgentSkillBinding, enabled: boolean) {
    if (!getAccessToken) {
      return;
    }

    setIsSavingKey(binding.skillKey);
    setError(null);

    try {
      await upsertChatAgentSkill(
        agent.id,
        { skillKey: binding.skillKey, enabled },
        { getAccessToken },
      );

      setBindings((current) =>
        current.map((item) =>
          item.skillKey === binding.skillKey ? { ...item, enabled } : item,
        ),
      );

      await loadSkills();
    } catch {
      setError(`Não foi possível ${enabled ? "ativar" : "desativar"} a skill ${binding.label}.`);
    } finally {
      setIsSavingKey(null);
    }
  }

  return (
    <section className="mdc-chat-agent-skills-page" aria-label="Skills do agente">
      <header className="mdc-chat-agent-skills-page__topbar">
        <button type="button" onClick={onBack}>
          <ArrowLeft size={18} aria-hidden="true" />
          <span>Voltar ao agente</span>
        </button>

        <div>
          <Sparkles size={18} aria-hidden="true" />
          <span>Skills — {agent.name}</span>
        </div>

        <button type="button" onClick={() => void loadSkills()} disabled={isLoading}>
          <RefreshCw size={16} aria-hidden="true" />
          <span>Atualizar</span>
        </button>
      </header>

      <div className="mdc-chat-agent-skills-page__intro">
        <p>
          <strong>Skills</strong> definem comportamentos do assistente (instruções de prompt).
          <strong> Actions</strong> executam APIs externas. Para rodar SQL no banco, habilite a
          skill e configure a action <code>POST /data/sql</code> em Actions.
        </p>
        <p className="mdc-chat-agent-skills-page__stats">
          {enabledCount} skill(s) ativa(s) de {bindings.length}
        </p>
      </div>

      {error ? <p className="mdc-chat-agent-skills-page__error">{error}</p> : null}

      {isLoading ? (
        <p className="mdc-chat-agent-skills-page__loading">Carregando skills…</p>
      ) : (
        <div className="mdc-chat-agent-skills-page__list">
          {bindings.map((binding) => {
            const sqlExecution = binding.derived?.sqlExecutionAvailable === true;

            return (
              <article key={binding.skillKey} className="mdc-chat-agent-skills-page__card">
                <div className="mdc-chat-agent-skills-page__card-head">
                  <span className="mdc-chat-agent-skills-page__icon">
                    <BookOpen size={18} aria-hidden="true" />
                  </span>

                  <div>
                    <strong>{binding.label}</strong>
                    <small>{binding.skillKey}</small>
                  </div>

                  <label className="mdc-chat-agent-skills-page__toggle">
                    <input
                      type="checkbox"
                      checked={binding.enabled}
                      disabled={isSavingKey === binding.skillKey}
                      onChange={(event) => void handleToggle(binding, event.target.checked)}
                    />
                    <span>{binding.enabled ? "Ativa" : "Inativa"}</span>
                  </label>
                </div>

                <p>{binding.description}</p>

                <div className="mdc-chat-agent-skills-page__meta">
                  <span>Policy: {binding.policyFile}</span>
                  {binding.executionHint ? (
                    <span>Execução: {binding.executionHint}</span>
                  ) : null}
                  {binding.skillKey === "sql" ? (
                    <span
                      className={
                        sqlExecution
                          ? "mdc-chat-agent-skills-page__badge is-ok"
                          : "mdc-chat-agent-skills-page__badge"
                      }
                    >
                      {sqlExecution
                        ? "Action SQL habilitada neste agente"
                        : "Action SQL não configurada"}
                    </span>
                  ) : null}
                </div>

                {binding.skillKey === "sql" && !sqlExecution && onOpenActions ? (
                  <button
                    type="button"
                    className="mdc-chat-agent-skills-page__link"
                    onClick={() => onOpenActions(agent)}
                  >
                    <Zap size={15} aria-hidden="true" />
                    <span>Configurar actions</span>
                  </button>
                ) : null}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
