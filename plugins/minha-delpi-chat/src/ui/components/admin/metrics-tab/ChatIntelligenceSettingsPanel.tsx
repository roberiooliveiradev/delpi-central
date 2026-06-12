import { useEffect, useState, type ReactNode } from "react";

import {
  getAdminChatIntelligenceSettings,
  reindexExternalActionEmbeddings,
  saveAdminChatIntelligenceSettings,
} from "../../../../data/api/adminApi";
import type {
  AdminChatIntelligenceSettings,
  AdminChatIntelligenceSettingsPayload,
} from "../../../../data/api/adminTypes";
import { AdminFormCheckbox } from "../shared/AdminFormCheckbox";
import {
  CHAT_INTELLIGENCE_NUMBER_META,
  CHAT_INTELLIGENCE_SECTIONS,
  CHAT_INTELLIGENCE_TOGGLE_META,
  QUALITY_IMPACT_LABELS,
  SPEED_IMPACT_LABELS,
  type ChatIntelligenceSettingMeta,
  type SettingQualityImpact,
  type SettingSpeedImpact,
} from "./chatIntelligenceSettingMeta";

import "./ChatIntelligenceSettingsPanel.css";

type ChatIntelligenceSettingsPanelProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

type ToggleKey = keyof typeof CHAT_INTELLIGENCE_TOGGLE_META;

function ImpactBadges({
  speed,
  quality,
  active,
}: {
  speed: SettingSpeedImpact;
  quality: SettingQualityImpact;
  active: boolean;
}) {
  if (!active) {
    return (
      <div className="mdc-chat-intelligence-setting__badges">
        <span className="mdc-chat-intelligence-impact mdc-chat-intelligence-impact--speed-neutral">
          Desligado
        </span>
      </div>
    );
  }

  return (
    <div className="mdc-chat-intelligence-setting__badges">
      <span
        className={`mdc-chat-intelligence-impact mdc-chat-intelligence-impact--speed-${speed}`}
      >
        {SPEED_IMPACT_LABELS[speed]}
      </span>
      <span
        className={`mdc-chat-intelligence-impact mdc-chat-intelligence-impact--quality-${quality}`}
      >
        {QUALITY_IMPACT_LABELS[quality]}
      </span>
    </div>
  );
}

function SettingProsCons({
  meta,
}: {
  meta: Pick<ChatIntelligenceSettingMeta, "pros" | "cons">;
}) {
  return (
    <div className="mdc-chat-intelligence-setting__lists">
      <div>
        <span className="mdc-chat-intelligence-setting__list-label">Prós</span>
        <ul className="mdc-chat-intelligence-setting__list">
          {meta.pros.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
      <div>
        <span className="mdc-chat-intelligence-setting__list-label">Contras</span>
        <ul className="mdc-chat-intelligence-setting__list">
          {meta.cons.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function ToggleSettingCard({
  meta,
  checked,
  onChange,
}: {
  meta: ChatIntelligenceSettingMeta;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <article className="mdc-chat-intelligence-setting">
      <div className="mdc-chat-intelligence-setting__head">
        <h5 className="mdc-chat-intelligence-setting__title">{meta.title}</h5>
        <ImpactBadges
          speed={meta.speedWhenEnabled}
          quality={meta.qualityWhenEnabled}
          active={checked}
        />
      </div>

      <p className="mdc-chat-intelligence-setting__summary">{meta.summary}</p>
      <SettingProsCons meta={meta} />

      {meta.tip ? (
        <p className="mdc-chat-intelligence-setting__tip">{meta.tip}</p>
      ) : null}

      <div className="mdc-chat-intelligence-setting__control">
        <AdminFormCheckbox
          title={checked ? "Ativado" : "Desativado"}
          hint="Marque para aplicar este comportamento no pipeline do chat."
          checked={checked}
          onChange={(event) => onChange(event.target.checked)}
        />
      </div>
    </article>
  );
}

function NumberSettingCard({
  fieldKey,
  value,
  onChange,
}: {
  fieldKey: keyof typeof CHAT_INTELLIGENCE_NUMBER_META;
  value: number;
  onChange: (value: number) => void;
}) {
  const meta = CHAT_INTELLIGENCE_NUMBER_META[fieldKey];

  return (
    <article className="mdc-chat-intelligence-setting">
      <div className="mdc-chat-intelligence-setting__head">
        <h5 className="mdc-chat-intelligence-setting__title">{meta.title}</h5>
      </div>

      <p className="mdc-chat-intelligence-setting__summary">{meta.summary}</p>
      <SettingProsCons meta={{ pros: meta.pros, cons: meta.cons }} />

      <div className="mdc-chat-intelligence-setting__notes">
        <p>
          <strong>Velocidade:</strong> {meta.speedNote}
        </p>
        <p>
          <strong>Qualidade:</strong> {meta.qualityNote}
        </p>
      </div>

      <div className="mdc-chat-intelligence-setting__control">
        <label className="mdc-admin-field">
          <span>Valor atual</span>
          <input
            type="number"
            min={meta.min}
            max={meta.max}
            step={meta.step}
            value={value}
            onChange={(event) => onChange(Number(event.target.value))}
          />
        </label>
      </div>
    </article>
  );
}

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

  function updateToggle(key: ToggleKey, checked: boolean) {
    setSettings({ ...settings!, [key]: checked });
  }

  async function handleSave() {
    setIsSaving(true);

    try {
      const { defaults: _defaults, source: _source, ...payload } = settings;
      const saved = await saveAdminChatIntelligenceSettings(
        payload as AdminChatIntelligenceSettingsPayload,
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

  const ragSection = (
    <>
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.ragHybridEnabled}
        checked={settings.ragHybridEnabled}
        onChange={(checked) => updateToggle("ragHybridEnabled", checked)}
      />
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.ragFtsEnabled}
        checked={settings.ragFtsEnabled}
        onChange={(checked) => updateToggle("ragFtsEnabled", checked)}
      />
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.ragRerankEnabled}
        checked={settings.ragRerankEnabled}
        onChange={(checked) => updateToggle("ragRerankEnabled", checked)}
      />
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.ragPreferKeywordSearch}
        checked={settings.ragPreferKeywordSearch}
        onChange={(checked) => updateToggle("ragPreferKeywordSearch", checked)}
      />
      <NumberSettingCard
        fieldKey="ragContextMinScore"
        value={settings.ragContextMinScore}
        onChange={(value) =>
          setSettings({ ...settings, ragContextMinScore: value })
        }
      />
      <NumberSettingCard
        fieldKey="ragIdentityQuestionMinScore"
        value={settings.ragIdentityQuestionMinScore}
        onChange={(value) =>
          setSettings({ ...settings, ragIdentityQuestionMinScore: value })
        }
      />
    </>
  );

  const actionsSection = (
    <>
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.operationalFastPathEnabled}
        checked={settings.operationalFastPathEnabled}
        onChange={(checked) => updateToggle("operationalFastPathEnabled", checked)}
      />
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.externalActionDirectResponseEnabled}
        checked={settings.externalActionDirectResponseEnabled}
        onChange={(checked) =>
          updateToggle("externalActionDirectResponseEnabled", checked)
        }
      />
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.preferApiExternaProvider}
        checked={settings.preferApiExternaProvider}
        onChange={(checked) => updateToggle("preferApiExternaProvider", checked)}
      />
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.multiActionEnabled}
        checked={settings.multiActionEnabled}
        onChange={(checked) => updateToggle("multiActionEnabled", checked)}
      />
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.paginationAutoFetchEnabled}
        checked={settings.paginationAutoFetchEnabled}
        onChange={(checked) => updateToggle("paginationAutoFetchEnabled", checked)}
      />
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.externalActionEmbeddingOnImport}
        checked={settings.externalActionEmbeddingOnImport}
        onChange={(checked) =>
          updateToggle("externalActionEmbeddingOnImport", checked)
        }
      />
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.externalActionSemanticRankEnabled}
        checked={settings.externalActionSemanticRankEnabled}
        onChange={(checked) =>
          updateToggle("externalActionSemanticRankEnabled", checked)
        }
      />
      <NumberSettingCard
        fieldKey="externalActionSemanticMinScore"
        value={settings.externalActionSemanticMinScore}
        onChange={(value) =>
          setSettings({ ...settings, externalActionSemanticMinScore: value })
        }
      />
    </>
  );

  const orchestrationSection = (
    <>
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.fastPathEnabled}
        checked={settings.fastPathEnabled}
        onChange={(checked) => updateToggle("fastPathEnabled", checked)}
      />
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.assistantIdentityDirectEnabled}
        checked={settings.assistantIdentityDirectEnabled}
        onChange={(checked) =>
          updateToggle("assistantIdentityDirectEnabled", checked)
        }
      />
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.chatToolRouterEnabled}
        checked={settings.chatToolRouterEnabled}
        onChange={(checked) => updateToggle("chatToolRouterEnabled", checked)}
      />
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.nativeToolCallingEnabled}
        checked={settings.nativeToolCallingEnabled}
        onChange={(checked) => updateToggle("nativeToolCallingEnabled", checked)}
      />
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.agenticLoopEnabled}
        checked={settings.agenticLoopEnabled}
        onChange={(checked) => updateToggle("agenticLoopEnabled", checked)}
      />
      <NumberSettingCard
        fieldKey="agenticLoopMaxSteps"
        value={settings.agenticLoopMaxSteps}
        onChange={(value) =>
          setSettings({ ...settings, agenticLoopMaxSteps: value })
        }
      />
    </>
  );

  const contextSection = (
    <ToggleSettingCard
      meta={CHAT_INTELLIGENCE_TOGGLE_META.chatHistorySummaryEnabled}
      checked={settings.chatHistorySummaryEnabled}
      onChange={(checked) => updateToggle("chatHistorySummaryEnabled", checked)}
    />
  );

  const toolsSection = (
    <>
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.webSearchEnabled}
        checked={settings.webSearchEnabled}
        onChange={(checked) => updateToggle("webSearchEnabled", checked)}
      />
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.webSearchDirectResponseEnabled}
        checked={settings.webSearchDirectResponseEnabled}
        onChange={(checked) =>
          updateToggle("webSearchDirectResponseEnabled", checked)
        }
      />
      <ToggleSettingCard
        meta={CHAT_INTELLIGENCE_TOGGLE_META.webSearchAutoAugmentEnabled}
        checked={settings.webSearchAutoAugmentEnabled}
        onChange={(checked) => updateToggle("webSearchAutoAugmentEnabled", checked)}
      />
    </>
  );

  const sectionContent: Record<string, ReactNode> = {
    rag: ragSection,
    actions: actionsSection,
    orchestration: orchestrationSection,
    context: contextSection,
    tools: toolsSection,
  };

  const sourceLabel =
    settings.source === "admin"
      ? "Configuração salva na administração"
      : "Usando padrões iniciais do servidor (Docker)";

  return (
    <article className="mdc-admin-kpi-card mdc-admin-kpi-card--wide mdc-chat-intelligence-panel">
      <h3>Inteligência do chat</h3>
      <p className="mdc-chat-intelligence-panel__intro">
        Cada opção abaixo altera o pipeline de RAG, seleção de actions ou orquestração
        do LLM. As alterações salvas aqui <strong>prevalecem</strong> sobre o arquivo
        <code> .env</code> do servidor — o Docker só define o padrão na primeira
        subida. Use os badges de velocidade e qualidade para decidir o que ativar em
        produção.
      </p>
      <p className="mdc-chat-intelligence-panel__source">{sourceLabel}</p>

      <div className="mdc-chat-intelligence-panel__sections">
        {CHAT_INTELLIGENCE_SECTIONS.map((section) => (
          <section key={section.id} className="mdc-chat-intelligence-section">
            <header className="mdc-chat-intelligence-section__header">
              <h4>{section.title}</h4>
              <p>{section.description}</p>
            </header>
            <div className="mdc-chat-intelligence-section__grid">
              {sectionContent[section.id]}
            </div>
          </section>
        ))}
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

      <p className="mdc-chat-intelligence-panel__reindex-note">
        Reindexar recalcula embeddings das actions no catálogo — necessário após criar,
        editar ou importar actions quando o ranking semântico estiver ativo.
      </p>

      {reindexResult ? <p className="mdc-chat-muted">{reindexResult}</p> : null}
    </article>
  );
}
