import { BarChart3, ExternalLink } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { getChatAgentStats } from "../../../../data/api/chatApi";
import { buildChatAgentConfigHref } from "../../../../navigation/chatRoutes";
import { navigateChatHref } from "../../../../navigation/chatNavigation";
import type { ChatAgentStats } from "../../../../data/api/chatTypes";
import {
  getAdminAgentSpecialization,
  listAdminAgentSpecializationPresets,
  listAdminSpecializedAgents,
  saveAdminAgentSpecialization,
} from "../../../../data/api/adminApi";
import type {
  AdminAgentSpecialization,
  AdminAgentSpecializationPreset,
  AdminSpecializedAgent,
} from "../../../../data/api/adminTypes";

import { AgentMiniDashboard } from "./AgentMiniDashboard";
import { AgentsSummaryStrip } from "./AgentsSummaryStrip";
import {
  computeAgentsSummary,
  filterAgentsByCatalog,
  type AgentCatalogFilter,
} from "./agentsSummary";

import "./AdminAgentsTab.css";

type AdminAgentsTabProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  initialAgentId?: string | null;
};

const EMPTY_SPECIALIZATION: AdminAgentSpecialization = {
  enabled: true,
  presetKey: "",
  label: "",
  domain: "",
  knowledgeDomains: [],
  knowledgeNamespaces: [],
  knowledgeCategories: [],
  knowledgeTags: [],
  guidelineCategories: [],
  allowedTools: [],
  includeGlobalKnowledge: true,
};

export function AdminAgentsTab({ getAccessToken, initialAgentId }: AdminAgentsTabProps) {
  const [agents, setAgents] = useState<AdminSpecializedAgent[]>([]);
  const [presets, setPresets] = useState<AdminAgentSpecializationPreset[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [form, setForm] = useState<AdminAgentSpecialization>(EMPTY_SPECIALIZATION);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [agentStats, setAgentStats] = useState<ChatAgentStats | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [catalogFilter, setCatalogFilter] = useState<AgentCatalogFilter>("all");

  const summary = useMemo(() => computeAgentsSummary(agents), [agents]);
  const visibleAgents = useMemo(
    () => filterAgentsByCatalog(agents, catalogFilter),
    [agents, catalogFilter],
  );

  const selectedAgent = agents.find((agent) => agent.id === selectedAgentId) ?? null;

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [agentsResponse, presetsResponse] = await Promise.all([
        listAdminSpecializedAgents({ getAccessToken }),
        listAdminAgentSpecializationPresets({ getAccessToken }),
      ]);

      setAgents(agentsResponse.items);
      setPresets(presetsResponse.presets);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar agentes.");
    } finally {
      setIsLoading(false);
    }
  }, [getAccessToken]);

  const loadAgentSpecialization = useCallback(
    async (agentId: string) => {
      try {
        const response = await getAdminAgentSpecialization(agentId, { getAccessToken });

        setForm(
          response.specialization
            ? {
                ...EMPTY_SPECIALIZATION,
                ...response.specialization,
              }
            : { ...EMPTY_SPECIALIZATION, enabled: false },
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao carregar especialização.");
      }
    },
    [getAccessToken],
  );

  useEffect(() => {
    void loadData();
  }, [loadData]);

  useEffect(() => {
    if (!initialAgentId || agents.length === 0) {
      return;
    }

    const match = agents.find((item) => item.id === initialAgentId);

    if (match) {
      setSelectedAgentId(match.id);
      void loadAgentSpecialization(match.id);
    }
  }, [agents, initialAgentId, loadAgentSpecialization]);

  useEffect(() => {
    if (!selectedAgentId) {
      return;
    }

    void loadAgentSpecialization(selectedAgentId);
  }, [loadAgentSpecialization, selectedAgentId]);

  useEffect(() => {
    let isMounted = true;

    async function loadStats() {
      if (!selectedAgentId || !getAccessToken) {
        setAgentStats(null);
        return;
      }

      setIsLoadingStats(true);

      try {
        const stats = await getChatAgentStats(selectedAgentId, {
          getAccessToken,
          hours: 168,
          specialization: form.enabled
            ? {
                enabled: true,
                allowedTools: form.allowedTools ?? [],
              }
            : { enabled: false, allowedTools: [] },
        });

        if (isMounted) {
          setAgentStats(stats);
        }
      } catch {
        if (isMounted) {
          setAgentStats(null);
        }
      } finally {
        if (isMounted) {
          setIsLoadingStats(false);
        }
      }
    }

    void loadStats();

    return () => {
      isMounted = false;
    };
  }, [form.allowedTools, form.enabled, getAccessToken, selectedAgentId]);

  function applyPreset(presetKey: string) {
    const preset = presets.find((item) => item.key === presetKey);

    if (!preset) {
      return;
    }

    setForm({
      enabled: true,
      presetKey: preset.key,
      label: preset.label,
      domain: preset.domain,
      knowledgeDomains: preset.knowledgeDomains ?? [],
      knowledgeNamespaces: preset.knowledgeNamespaces ?? [],
      knowledgeCategories: preset.knowledgeCategories ?? [],
      knowledgeTags: preset.knowledgeTags ?? [],
      guidelineCategories: preset.guidelineCategories ?? [],
      allowedTools: preset.allowedTools ?? [],
      includeGlobalKnowledge: preset.includeGlobalKnowledge ?? true,
    });
  }

  function updateListField(
    key:
      | "knowledgeDomains"
      | "knowledgeNamespaces"
      | "knowledgeCategories"
      | "knowledgeTags"
      | "guidelineCategories"
      | "allowedTools",
    value: string,
  ) {
    setForm((current) => ({
      ...current,
      [key]: value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
    }));
  }

  async function handleSave() {
    if (!selectedAgentId) {
      return;
    }

    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await saveAdminAgentSpecialization(
        {
          specialization: form.enabled ? form : { enabled: false },
        },
        selectedAgentId,
        { getAccessToken },
      );

      setSuccessMessage("Especialização do agente salva.");
      await loadData();
      await loadAgentSpecialization(selectedAgentId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar especialização.");
    } finally {
      setIsSaving(false);
    }
  }

  function openAgentBuilder() {
    if (!selectedAgentId) {
      return;
    }

    navigateChatHref(buildChatAgentConfigHref(selectedAgentId));
  }

  return (
    <section className="mdc-admin-agents">
      <header className="mdc-admin-page-header">
        <h2>Agentes especializados</h2>
        <p className="mdc-chat-muted">
          Configure domínio, escopo de RAG, diretrizes e tools permitidas por agente oficial. Para
          identidade, prompt e actions, use o builder do agente.
        </p>
      </header>

      <div className="mdc-admin-agents__toolbar">
        <AgentsSummaryStrip
          summary={summary}
          activeFilter={catalogFilter}
          isLoading={isLoading}
          onFilterChange={setCatalogFilter}
        />

        <div className="mdc-admin-agents__toolbar-actions">
          <button
            type="button"
            className="mdc-admin-btn"
            disabled={isLoading}
            onClick={() => void loadData()}
          >
            {isLoading ? "Carregando..." : "Atualizar"}
          </button>
          <button
            type="button"
            className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
            disabled={!selectedAgentId}
            onClick={openAgentBuilder}
          >
            <ExternalLink size={15} aria-hidden="true" />
            <span>Abrir builder</span>
          </button>
        </div>
      </div>

      {error ? <p className="mdc-admin-agents__error">{error}</p> : null}
      {successMessage ? <p className="mdc-admin-agents__success">{successMessage}</p> : null}

      <div className="mdc-admin-agents__layout mdc-admin-split">
        <aside className="mdc-admin-split__aside mdc-admin-agents__list">
          {isLoading ? (
            <p className="mdc-chat-muted">Carregando agentes…</p>
          ) : visibleAgents.length === 0 ? (
            <p className="mdc-chat-muted">
              {agents.length === 0
                ? "Nenhum agente oficial disponível."
                : "Nenhum agente neste filtro."}
            </p>
          ) : (
          <ul>
            {visibleAgents.map((agent) => (
              <li key={agent.id}>
                <button
                  type="button"
                  className={selectedAgentId === agent.id ? "is-selected" : undefined}
                  onClick={() => setSelectedAgentId(agent.id)}
                >
                  <strong>{agent.name}</strong>
                  <span>{agent.id}</span>
                  <small>{agent.hasSpecialization ? "Especializado" : "Sem especialização"}</small>
                </button>
              </li>
            ))}
          </ul>
          )}
        </aside>

        <article className="mdc-admin-split__main mdc-admin-agents__editor">
          {!selectedAgent ? (
            <p className="mdc-chat-muted">Selecione um agente para configurar a especialização.</p>
          ) : (
            <>
              <div className="mdc-admin-agents__agent-title">
                <strong>{selectedAgent.name}</strong>
                <span>{selectedAgent.id}</span>
              </div>

              <div className="mdc-admin-agents__stats">
                <div className="mdc-admin-agents__stats-title">
                  <BarChart3 size={16} aria-hidden="true" />
                  <span>Uso (últimos 7 dias)</span>
                </div>
                {isLoadingStats ? (
                  <p className="mdc-chat-muted">Carregando estatísticas...</p>
                ) : agentStats?.miniDashboard ? (
                  <AgentMiniDashboard stats={agentStats} />
                ) : agentStats ? (
                  <p className="mdc-chat-muted">
                    Estatísticas disponíveis, mas o painel visual não foi retornado pela API.
                  </p>
                ) : (
                  <p className="mdc-chat-muted">Sem dados de uso no período.</p>
                )}
              </div>

              <label className="mdc-admin-agents__toggle">
                <input
                  type="checkbox"
                  checked={form.enabled}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, enabled: event.target.checked }))
                  }
                />
                Especialização ativa
              </label>

              {form.enabled ? (
                <>
                  <label>
                    <span>Preset de domínio</span>
                    <select
                      value={form.presetKey ?? ""}
                      onChange={(event) => {
                        const value = event.target.value;
                        setForm((current) => ({ ...current, presetKey: value }));
                        if (value) {
                          applyPreset(value);
                        }
                      }}
                    >
                      <option value="">Personalizado</option>
                      {presets.map((preset) => (
                        <option key={preset.key} value={preset.key}>
                          {preset.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <div className="mdc-admin-agents__grid">
                    <label>
                      <span>Rótulo</span>
                      <input
                        value={form.label ?? ""}
                        onChange={(event) =>
                          setForm((current) => ({ ...current, label: event.target.value }))
                        }
                      />
                    </label>
                    <label>
                      <span>Domínio</span>
                      <input
                        value={form.domain ?? ""}
                        onChange={(event) =>
                          setForm((current) => ({ ...current, domain: event.target.value }))
                        }
                      />
                    </label>
                  </div>

                  <label>
                    <span>Domínios de conhecimento (vírgula)</span>
                    <input
                      value={(form.knowledgeDomains ?? []).join(", ")}
                      onChange={(event) => updateListField("knowledgeDomains", event.target.value)}
                    />
                  </label>

                  <label>
                    <span>Namespaces (vírgula)</span>
                    <input
                      value={(form.knowledgeNamespaces ?? []).join(", ")}
                      onChange={(event) => updateListField("knowledgeNamespaces", event.target.value)}
                    />
                  </label>

                  <label>
                    <span>Categorias de conhecimento (vírgula)</span>
                    <input
                      value={(form.knowledgeCategories ?? []).join(", ")}
                      onChange={(event) => updateListField("knowledgeCategories", event.target.value)}
                    />
                  </label>

                  <label>
                    <span>Tags de conhecimento (vírgula)</span>
                    <input
                      value={(form.knowledgeTags ?? []).join(", ")}
                      onChange={(event) => updateListField("knowledgeTags", event.target.value)}
                    />
                  </label>

                  <label>
                    <span>Categorias de diretrizes (vírgula)</span>
                    <input
                      value={(form.guidelineCategories ?? []).join(", ")}
                      onChange={(event) => updateListField("guidelineCategories", event.target.value)}
                    />
                  </label>

                  <label>
                    <span>Tools permitidas (vírgula)</span>
                    <input
                      value={(form.allowedTools ?? []).join(", ")}
                      onChange={(event) => updateListField("allowedTools", event.target.value)}
                    />
                  </label>

                  <label className="mdc-admin-agents__toggle">
                    <input
                      type="checkbox"
                      checked={form.includeGlobalKnowledge ?? true}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          includeGlobalKnowledge: event.target.checked,
                        }))
                      }
                    />
                    Incluir base global além do domínio
                  </label>
                </>
              ) : null}

              <button
                type="button"
                className="mdc-admin-btn mdc-admin-btn--primary"
                disabled={isSaving}
                onClick={() => void handleSave()}
              >
                {isSaving ? "Salvando..." : "Salvar especialização"}
              </button>
            </>
          )}
        </article>
      </div>
    </section>
  );
}
