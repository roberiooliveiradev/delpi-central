import { useEffect, useMemo, useState } from "react";
import { LayoutTemplate, Save } from "lucide-react";
import {
  listPublishedSlideTemplates,
  type SlideTemplate,
} from "../../api/tvDashboardApi";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import {
  COMUNICADO_SLIDE_THEMES,
  type ComunicadoSlideTheme,
} from "../../content/comunicadoSlideThemes";
import { DeckPropertySection } from "./DeckPropertySection";
import { DeckSettingsAccordion } from "./DeckSettingsAccordion";
import { SaveAsTemplateModal } from "../SaveAsTemplateModal";
import { TemplateThumb } from "../TemplateThumb";
import { useTvDashboardSession } from "../../context/TvDashboardSessionContext";
import type { CSSProperties } from "react";

function themeSwatchLabelStyle(theme: ComunicadoSlideTheme): CSSProperties {
  const color = theme.textColor;
  const isLightText = /^#f|^#e|^#fff|white/i.test(color.trim());
  return {
    color,
    textShadow: isLightText ? "0 1px 2px rgba(0, 0, 0, 0.55)" : "none",
  };
}

type Props = {
  compact?: boolean;
};

/**
 * Painel Aplicar: só templates **published** do Postgres (cutover).
 * Import/Export MDD ficam na Biblioteca (templates.manage).
 */
export function ComunicadoSlideTemplatesPanel({ compact = false }: Props) {
  const { config, applySlideTemplate, applySlideTheme } = useComunicadoEditor();
  const { canManageTemplates: canSaveAs } = useTvDashboardSession();
  const [templates, setTemplates] = useState<SlideTemplate[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [applyingId, setApplyingId] = useState<string | null>(null);
  const [saveOpen, setSaveOpen] = useState(false);

  useEffect(() => {
    void listPublishedSlideTemplates()
      .then(setTemplates)
      .catch((err: Error) => setError(err.message));
  }, []);

  const published = useMemo(
    () =>
      templates.filter(
        (item) =>
          item.status === "published" &&
          (item.nativeScreenKey === "custom_message" || !item.nativeScreenKey),
      ),
    [templates],
  );

  async function applyTemplate(item: SlideTemplate) {
    setApplyingId(item.id);
    setError(null);
    try {
      // Cópia no slide — não muta o master.
      if (item.nativeConfig) applySlideTemplate(item.nativeConfig);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao aplicar template.");
    } finally {
      setApplyingId(null);
    }
  }

  const body = (
    <>
      <DeckPropertySection
        title="Templates"
        hint="Aplica uma cópia do template publicado no slide atual."
        compact={compact}
      >
        {error ? <p className="td-error">{error}</p> : null}
        {published.length === 0 && !error ? (
          <p className="td-template-list__empty">Nenhum template publicado.</p>
        ) : null}
        <ul className="td-template-list">
          {published.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className="td-template-list__item td-template-list__item--with-thumb"
                disabled={applyingId === item.id}
                onClick={() => void applyTemplate(item)}
              >
                <span className="td-template-list__thumb">
                  <TemplateThumb template={item} />
                </span>
                <span className="td-template-list__label">
                  {applyingId === item.id ? "Aplicando…" : item.label}
                </span>
                {!compact && item.description ? (
                  <span className="td-template-list__meta">{item.description}</span>
                ) : null}
              </button>
            </li>
          ))}
        </ul>
        {canSaveAs ? (
          <div className="td-template-mdd-actions">
            <button
              type="button"
              className="td-template-mdd-actions__btn"
              onClick={() => setSaveOpen(true)}
            >
              <Save size={14} aria-hidden="true" />
              Salvar slide como template…
            </button>
          </div>
        ) : null}
      </DeckPropertySection>

      <DeckPropertySection title="Temas de cor" hint="Aplica paleta ao fundo e aos blocos de texto/forma." compact={compact}>
        <div className="td-theme-grid">
          {COMUNICADO_SLIDE_THEMES.map((theme) => (
            <button
              key={theme.key}
              type="button"
              className="td-theme-swatch"
              title={theme.label}
              onClick={() => applySlideTheme(theme)}
              style={{
                backgroundImage:
                  theme.background.type === "gradient"
                    ? `linear-gradient(135deg, ${theme.background.from}, ${theme.background.to})`
                    : undefined,
                backgroundColor:
                  theme.background.type === "color" ? theme.background.value : undefined,
              }}
            >
              <span style={themeSwatchLabelStyle(theme)}>{theme.label}</span>
            </button>
          ))}
        </div>
      </DeckPropertySection>

      <SaveAsTemplateModal
        open={saveOpen}
        nativeConfig={config as unknown as Record<string, unknown>}
        onClose={() => setSaveOpen(false)}
      />
    </>
  );

  if (compact) {
    return (
      <DeckSettingsAccordion
        summary="Templates"
        ariaLabel="Templates e temas do slide"
        icon={LayoutTemplate}
      >
        {body}
      </DeckSettingsAccordion>
    );
  }

  return body;
}
