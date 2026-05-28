import { useEffect, useState } from "react";

import {
  getAdminChatIntelligenceSettings,
  reindexExternalActionEmbeddings,
  saveAdminChatIntelligenceSettings,
} from "../../../../data/api/adminApi";
import type { AdminChatIntelligenceSettings } from "../../../../data/api/adminTypes";
import { AdminFormCheckbox } from "../shared/AdminFormCheckbox";

type ChatIntelligenceSettingsPanelProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function ChatIntelligenceSettingsPanel({
  getAccessToken,
}: ChatIntelligenceSettingsPanelProps) {
  const [settings, setSettings] = useState<AdminChatIntelligenceSettings | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isReindexing, setIsReindexing] = useState(false);
  const [reindexResult, setReindexResult] = useState<string | null>(null);

  useEffect(() => {
    if (!getAccessToken) {
      return;
    }

    void getAdminChatIntelligenceSettings({ getAccessToken })
      .then(setSettings)
      .catch(() => setSettings(null));
  }, [getAccessToken]);

  if (!getAccessToken || !settings) {
    return null;
  }

  async function handleSave() {
    setIsSaving(true);

    try {
      const saved = await saveAdminChatIntelligenceSettings(
        {
          ragContextMinScore: settings.ragContextMinScore,
          externalActionSemanticMinScore: settings.externalActionSemanticMinScore,
          externalActionSemanticRankEnabled: settings.externalActionSemanticRankEnabled,
          chatToolRouterEnabled: settings.chatToolRouterEnabled,
          chatHistorySummaryEnabled: settings.chatHistorySummaryEnabled,
          ragHybridEnabled: settings.ragHybridEnabled,
          ragRerankEnabled: settings.ragRerankEnabled,
          ragFtsEnabled: settings.ragFtsEnabled,
          nativeToolCallingEnabled: settings.nativeToolCallingEnabled,
          agenticLoopEnabled: settings.agenticLoopEnabled,
          agenticLoopMaxSteps: settings.agenticLoopMaxSteps,
        },
        { getAccessToken },
      );
      setSettings(saved);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleReindex() {
    setIsReindexing(true);
    setReindexResult(null);

    try {
      const result = await reindexExternalActionEmbeddings({}, { getAccessToken });
      setReindexResult(
        `Embeddings atualizados: ${result.updated} · ignorados: ${result.skipped} · total: ${result.total}`,
      );
    } catch {
      setReindexResult("Não foi possível reindexar embeddings das actions.");
    } finally {
      setIsReindexing(false);
    }
  }

  return (
    <article className="mdc-admin-kpi-card mdc-admin-kpi-card--wide">
      <h3>Inteligência do chat</h3>
      <p className="mdc-chat-muted">
        Limiares e recursos de inteligência (RAG, actions, router, loop agentic).
      </p>

      <div className="mdc-admin-metrics-tab__intelligence-form">
        <label className="mdc-admin-field">
          <span>Score mínimo RAG</span>
          <input
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={settings.ragContextMinScore}
            onChange={(event) =>
              setSettings({
                ...settings,
                ragContextMinScore: Number(event.target.value),
              })
            }
          />
        </label>

        <label className="mdc-admin-field">
          <span>Score mínimo action semântica</span>
          <input
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={settings.externalActionSemanticMinScore}
            onChange={(event) =>
              setSettings({
                ...settings,
                externalActionSemanticMinScore: Number(event.target.value),
              })
            }
          />
        </label>

        <AdminFormCheckbox
          title="Ranking semântico de actions"
          checked={settings.externalActionSemanticRankEnabled}
          onChange={(event) =>
            setSettings({
              ...settings,
              externalActionSemanticRankEnabled: event.target.checked,
            })
          }
        />

        <AdminFormCheckbox
          title="Router LLM de ferramentas"
          checked={settings.chatToolRouterEnabled}
          onChange={(event) =>
            setSettings({
              ...settings,
              chatToolRouterEnabled: event.target.checked,
            })
          }
        />

        <AdminFormCheckbox
          title="Resumo de histórico longo"
          checked={settings.chatHistorySummaryEnabled}
          onChange={(event) =>
            setSettings({
              ...settings,
              chatHistorySummaryEnabled: event.target.checked,
            })
          }
        />

        <AdminFormCheckbox
          title="RAG híbrido (vetor + palavras-chave)"
          checked={settings.ragHybridEnabled}
          onChange={(event) =>
            setSettings({
              ...settings,
              ragHybridEnabled: event.target.checked,
            })
          }
        />

        <AdminFormCheckbox
          title="Rerank pós-híbrido no RAG"
          checked={settings.ragRerankEnabled}
          onChange={(event) =>
            setSettings({
              ...settings,
              ragRerankEnabled: event.target.checked,
            })
          }
        />

        <AdminFormCheckbox
          title="Busca FTS no Postgres (keyword RAG)"
          checked={settings.ragFtsEnabled}
          onChange={(event) =>
            setSettings({
              ...settings,
              ragFtsEnabled: event.target.checked,
            })
          }
        />

        <AdminFormCheckbox
          title="Tool-calling nativo do LLM (vLLM/Ollama)"
          checked={settings.nativeToolCallingEnabled}
          onChange={(event) =>
            setSettings({
              ...settings,
              nativeToolCallingEnabled: event.target.checked,
            })
          }
        />

        <AdminFormCheckbox
          title="Loop agentic de ferramentas"
          checked={settings.agenticLoopEnabled}
          onChange={(event) =>
            setSettings({
              ...settings,
              agenticLoopEnabled: event.target.checked,
            })
          }
        />

        <label className="mdc-admin-field">
          <span>Máx. passos do loop agentic</span>
          <input
            type="number"
            min={1}
            max={3}
            step={1}
            value={settings.agenticLoopMaxSteps}
            onChange={(event) =>
              setSettings({
                ...settings,
                agenticLoopMaxSteps: Number(event.target.value),
              })
            }
          />
        </label>
      </div>

      <div className="mdc-admin-metrics-tab__intelligence-actions">
        <button
          type="button"
          className="mdc-admin-btn mdc-admin-btn--primary"
          disabled={isSaving}
          onClick={() => void handleSave()}
        >
          {isSaving ? "Salvando..." : "Salvar configurações"}
        </button>
        <button
          type="button"
          className="mdc-admin-btn"
          disabled={isReindexing}
          onClick={() => void handleReindex()}
        >
          {isReindexing ? "Reindexando..." : "Reindexar embeddings das actions"}
        </button>
      </div>

      {reindexResult ? <p className="mdc-chat-muted">{reindexResult}</p> : null}
    </article>
  );
}
