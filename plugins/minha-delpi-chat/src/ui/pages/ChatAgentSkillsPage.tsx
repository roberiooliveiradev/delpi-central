import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  Circle,
  Database,
  RefreshCw,
  Sparkles,
  Zap,
} from "lucide-react";
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

function SkillStatusPill({
  enabled,
  saving,
}: {
  enabled: boolean;
  saving: boolean;
}) {
  return (
    <span
      className={[
        "mdc-agent-skills__pill",
        enabled ? "mdc-agent-skills__pill--on" : "mdc-agent-skills__pill--off",
        saving ? "mdc-agent-skills__pill--saving" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {enabled ? (
        <CheckCircle2 size={13} aria-hidden="true" />
      ) : (
        <Circle size={13} aria-hidden="true" />
      )}
      <span>{saving ? "Salvando…" : enabled ? "Ativa" : "Inativa"}</span>
    </span>
  );
}

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
    <section className="mdc-agent-skills" aria-label="Skills do agente">
      <header className="mdc-agent-skills__topbar">
        <button type="button" className="mdc-agent-skills__back" onClick={onBack}>
          <ArrowLeft size={18} aria-hidden="true" />
          <span>Voltar</span>
        </button>

        <div className="mdc-agent-skills__topbar-title">
          <Sparkles size={17} aria-hidden="true" />
          <div>
            <span>Skills</span>
            <small>{agent.name}</small>
          </div>
        </div>

        <button
          type="button"
          className="mdc-agent-skills__refresh"
          onClick={() => void loadSkills()}
          disabled={isLoading}
          aria-label="Atualizar lista"
        >
          <RefreshCw size={16} aria-hidden="true" className={isLoading ? "is-spinning" : ""} />
        </button>
      </header>

      <div className="mdc-agent-skills__body">
        <aside className="mdc-agent-skills__callout">
          <p>
            <strong>Skills</strong> orientam o comportamento do assistente (prompt).{" "}
            <strong>Actions</strong> executam APIs. Para SQL no banco, ative a skill e a action{" "}
            <code>POST /data/sql</code>.
          </p>
          <div className="mdc-agent-skills__stats">
            <span className="mdc-agent-skills__stat">
              <strong>{enabledCount}</strong>
              <small>ativas</small>
            </span>
            <span className="mdc-agent-skills__stat-divider" aria-hidden="true" />
            <span className="mdc-agent-skills__stat">
              <strong>{bindings.length}</strong>
              <small>no catálogo</small>
            </span>
          </div>
        </aside>

        {error ? (
          <p className="mdc-agent-skills__error" role="alert">
            {error}
          </p>
        ) : null}

        {isLoading ? (
          <div className="mdc-agent-skills__list" aria-busy="true">
            {[0, 1].map((index) => (
              <div key={index} className="mdc-agent-skills__card mdc-agent-skills__card--skeleton" />
            ))}
          </div>
        ) : bindings.length === 0 ? (
          <div className="mdc-agent-skills__empty">
            <BookOpen size={28} aria-hidden="true" />
            <strong>Nenhuma skill no catálogo</strong>
            <p>O catálogo é definido na API; entre em contato com o administrador se esperava itens aqui.</p>
          </div>
        ) : (
          <div className="mdc-agent-skills__list">
            {bindings.map((binding) => {
              const sqlExecution = binding.derived?.sqlExecutionAvailable === true;
              const isSaving = isSavingKey === binding.skillKey;

              return (
                <article
                  key={binding.skillKey}
                  className={[
                    "mdc-agent-skills__card",
                    binding.enabled ? "mdc-agent-skills__card--on" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  <div className="mdc-agent-skills__card-main">
                    <span className="mdc-agent-skills__icon" aria-hidden="true">
                      {binding.skillKey === "sql" ? (
                        <Database size={18} />
                      ) : (
                        <BookOpen size={18} />
                      )}
                    </span>

                    <div className="mdc-agent-skills__card-copy">
                      <div className="mdc-agent-skills__card-headline">
                        <h3>{binding.label}</h3>
                        <SkillStatusPill enabled={binding.enabled} saving={isSaving} />
                      </div>
                      <p>{binding.description}</p>
                    </div>

                    <label className="mdc-agent-skills__switch">
                      <input
                        type="checkbox"
                        checked={binding.enabled}
                        disabled={isSaving}
                        onChange={(event) => void handleToggle(binding, event.target.checked)}
                      />
                      <span className="mdc-agent-skills__switch-track" aria-hidden="true" />
                      <span className="sr-only">
                        {binding.enabled ? "Desativar" : "Ativar"} {binding.label}
                      </span>
                    </label>
                  </div>

                  <footer className="mdc-agent-skills__card-foot">
                    {binding.skillKey === "sql" ? (
                      <span
                        className={[
                          "mdc-agent-skills__tag",
                          sqlExecution ? "mdc-agent-skills__tag--ok" : "",
                        ]
                          .filter(Boolean)
                          .join(" ")}
                      >
                        {sqlExecution ? "Execução SQL configurada" : "Sem action SQL no agente"}
                      </span>
                    ) : null}

                    {binding.executionHint ? (
                      <span className="mdc-agent-skills__tag mdc-agent-skills__tag--muted">
                        {binding.executionHint}
                      </span>
                    ) : null}

                    {binding.skillKey === "sql" && !sqlExecution && onOpenActions ? (
                      <button
                        type="button"
                        className="mdc-agent-skills__cta"
                        onClick={() => onOpenActions(agent)}
                      >
                        <Zap size={14} aria-hidden="true" />
                        <span>Abrir actions</span>
                      </button>
                    ) : null}
                  </footer>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
