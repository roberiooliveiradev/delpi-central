import { useEffect, useState, type ReactNode } from "react";

import { AdminFormCheckbox } from "../shared/AdminFormCheckbox";
import {
  QUALITY_IMPACT_LABELS,
  SPEED_IMPACT_LABELS,
  type ChatIntelligenceSettingMeta,
  type SettingQualityImpact,
  type SettingSpeedImpact,
} from "./chatIntelligenceSettingMeta";

import "./ChatIntelligenceSettingsPanel.css";

export type AdminBundleNumberMeta = {
  title: string;
  summary: string;
  pros: readonly string[];
  cons: readonly string[];
  speedNote: string;
  qualityNote: string;
  min: number;
  max: number;
  step: number;
};

export type AdminBundleSectionMeta = {
  id: string;
  title: string;
  description: string;
};

type BundleSettingsRecord = Record<string, unknown> & {
  source?: string;
  defaults?: Record<string, unknown>;
};

type ChatAdminBundleSettingsPanelProps<T extends BundleSettingsRecord> = {
  title: string;
  intro: string;
  sections: AdminBundleSectionMeta[];
  renderSection: (
    settings: T,
    updateField: (key: string, value: unknown) => void,
    sectionId: string,
  ) => ReactNode;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  loadSettings: (
    options: { getAccessToken?: ChatAdminBundleSettingsPanelProps<T>["getAccessToken"] },
  ) => Promise<T>;
  saveSettings: (
    payload: Partial<T>,
    options: { getAccessToken?: ChatAdminBundleSettingsPanelProps<T>["getAccessToken"] },
  ) => Promise<T>;
};

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

export function BundleToggleSettingCard({
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

export function BundleNumberSettingCard({
  meta,
  value,
  onChange,
}: {
  meta: AdminBundleNumberMeta;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <article className="mdc-chat-intelligence-setting">
      <div className="mdc-chat-intelligence-setting__head">
        <h5 className="mdc-chat-intelligence-setting__title">{meta.title}</h5>
      </div>

      <p className="mdc-chat-intelligence-setting__summary">{meta.summary}</p>

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

export function ChatAdminBundleSettingsPanel<T extends BundleSettingsRecord>({
  title,
  intro,
  sections,
  renderSection,
  getAccessToken,
  loadSettings,
  saveSettings,
}: ChatAdminBundleSettingsPanelProps<T>) {
  const [settings, setSettings] = useState<T | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (!getAccessToken) {
      return;
    }

    void loadSettings({ getAccessToken })
      .then(setSettings)
      .catch(() => setSettings(null));
  }, [getAccessToken, loadSettings]);

  if (!getAccessToken || !settings) {
    return null;
  }

  function updateField(key: string, value: unknown) {
    setSettings({ ...settings!, [key]: value });
  }

  async function handleSave() {
    setIsSaving(true);

    try {
      const { defaults: _defaults, source: _source, ...payload } = settings!;
      const saved = await saveSettings(payload as Partial<T>, { getAccessToken });
      setSettings(saved);
    } finally {
      setIsSaving(false);
    }
  }

  const sourceLabel =
    settings.source === "admin"
      ? "Valores ativos salvos na administração (prevalecem sobre o .env do Docker)."
      : "Usando defaults iniciais do ambiente — salve para gravar na administração.";

  const sectionContent: Record<string, ReactNode> = {};
  for (const section of sections) {
    sectionContent[section.id] = renderSection(settings, updateField, section.id);
  }

  return (
    <article className="mdc-admin-kpi-card mdc-admin-kpi-card--wide mdc-chat-intelligence-panel">
      <h4>{title}</h4>
      <p className="mdc-chat-intelligence-panel__intro">{intro}</p>
      <p className="mdc-chat-intelligence-panel__source">{sourceLabel}</p>

      <div className="mdc-chat-intelligence-panel__sections">
        {sections.map((section) => (
          <section key={section.id} className="mdc-chat-intelligence-section">
            <header className="mdc-chat-intelligence-section__header">
              <h5>{section.title}</h5>
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
          className="mdc-admin-button mdc-admin-button--primary"
          disabled={isSaving}
          onClick={() => void handleSave()}
        >
          {isSaving ? "Salvando…" : "Salvar configurações"}
        </button>
      </div>
    </article>
  );
}
