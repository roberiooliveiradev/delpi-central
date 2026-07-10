import { useEffect, useMemo, useState } from "react";
import { getSlidePreset, listSlidePresets, type SlidePreset } from "../../api/tvDashboardApi";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { COMUNICADO_SLIDE_THEMES } from "../../content/comunicadoSlideThemes";
import { DeckPropertySection } from "./DeckPropertySection";
import { DeckSettingsAccordion } from "./DeckSettingsAccordion";

export function ComunicadoSlideTemplatesPanel({ compact = false }: { compact?: boolean }) {
  const { applySlideTemplate, applySlideTheme } = useComunicadoEditor();
  const [presets, setPresets] = useState<SlidePreset[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [applyingKey, setApplyingKey] = useState<string | null>(null);

  useEffect(() => {
    void listSlidePresets()
      .then(setPresets)
      .catch((err: Error) => setError(err.message));
  }, []);

  const comunicadoPresets = useMemo(
    () =>
      presets.filter(
        (preset) =>
          preset.slideType === "native" &&
          preset.key.startsWith("preset_comunicado") &&
          preset.key !== "preset_comunicado",
      ),
    [presets],
  );

  async function applyPreset(presetKey: string) {
    setApplyingKey(presetKey);
    setError(null);
    try {
      const detail = await getSlidePreset(presetKey);
      if (detail.nativeConfig) applySlideTemplate(detail.nativeConfig);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar template.");
    } finally {
      setApplyingKey(null);
    }
  }

  const body = (
    <>
      <DeckPropertySection title="Templates" hint="Substitui o conteúdo do slide pelo layout do template." compact={compact}>
        {error ? <p className="td-error">{error}</p> : null}
        <ul className="td-template-list">
          {comunicadoPresets.map((preset) => (
            <li key={preset.key}>
              <button
                type="button"
                className="td-template-list__item"
                disabled={applyingKey === preset.key}
                onClick={() => void applyPreset(preset.key)}
              >
                <span className="td-template-list__label">
                  {applyingKey === preset.key ? "Aplicando…" : preset.label}
                </span>
                {!compact && preset.description ? (
                  <span className="td-template-list__meta">{preset.description}</span>
                ) : null}
              </button>
            </li>
          ))}
        </ul>
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
              <span>{theme.label}</span>
            </button>
          ))}
        </div>
      </DeckPropertySection>
    </>
  );

  if (compact) {
    return (
      <DeckSettingsAccordion summary="Templates" ariaLabel="Templates e temas do slide">
        {body}
      </DeckSettingsAccordion>
    );
  }

  return body;
}
