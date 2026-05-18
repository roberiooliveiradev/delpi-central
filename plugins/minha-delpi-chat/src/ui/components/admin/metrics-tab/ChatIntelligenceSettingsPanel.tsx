import { useEffect, useState } from "react";

import {
  getAdminChatIntelligenceSettings,
  reindexExternalActionEmbeddings,
  saveAdminChatIntelligenceSettings,
} from "../../../../data/api/adminApi";
import type { AdminChatIntelligenceSettings } from "../../../../data/api/adminTypes";

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
    <article className="mdc-admin-metrics-card mdc-admin-metrics-card--wide">
      <h3>Inteligência do chat</h3>
      <p className="mdc-chat-muted">
        Limiares e recursos da Onda 2 (RAG, actions semânticas, router e resumo de histórico).
      </p>

      <div className="mdc-admin-metrics-tab__intelligence-form">
        <label>
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

        <label>
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

        <label className="mdc-admin-metrics-tab__checkbox">
          <input
            type="checkbox"
            checked={settings.externalActionSemanticRankEnabled}
            onChange={(event) =>
              setSettings({
                ...settings,
                externalActionSemanticRankEnabled: event.target.checked,
              })
            }
          />
          <span>Ranking semântico de actions</span>
        </label>

        <label className="mdc-admin-metrics-tab__checkbox">
          <input
            type="checkbox"
            checked={settings.chatToolRouterEnabled}
            onChange={(event) =>
              setSettings({
                ...settings,
                chatToolRouterEnabled: event.target.checked,
              })
            }
          />
          <span>Router LLM de ferramentas</span>
        </label>

        <label className="mdc-admin-metrics-tab__checkbox">
          <input
            type="checkbox"
            checked={settings.chatHistorySummaryEnabled}
            onChange={(event) =>
              setSettings({
                ...settings,
                chatHistorySummaryEnabled: event.target.checked,
              })
            }
          />
          <span>Resumo de histórico longo</span>
        </label>
      </div>

      <div className="mdc-admin-metrics-tab__intelligence-actions">
        <button type="button" disabled={isSaving} onClick={() => void handleSave()}>
          {isSaving ? "Salvando..." : "Salvar configurações"}
        </button>
        <button type="button" disabled={isReindexing} onClick={() => void handleReindex()}>
          {isReindexing ? "Reindexando..." : "Reindexar embeddings das actions"}
        </button>
      </div>

      {reindexResult ? <p className="mdc-chat-muted">{reindexResult}</p> : null}
    </article>
  );
}
