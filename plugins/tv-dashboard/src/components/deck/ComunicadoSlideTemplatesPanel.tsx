import { useEffect, useMemo, useRef, useState } from "react";
import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";

import { getSlidePreset, listSlidePresets, type SlidePreset } from "../../api/tvDashboardApi";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { COMUNICADO_SLIDE_THEMES } from "../../content/comunicadoSlideThemes";
import { DeckPropertySection } from "./DeckPropertySection";

export function ComunicadoSlideTemplatesPanel({ compact = false }: { compact?: boolean }) {
  const { applySlideTemplate, applySlideTheme } = useComunicadoEditor();
  const [presets, setPresets] = useState<SlidePreset[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [applyingKey, setApplyingKey] = useState<string | null>(null);
  const [accordionOpen, setAccordionOpen] = useState(false);
  const accordionAnchorRef = useRef<HTMLDivElement>(null);
  const accordionPanelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    void listSlidePresets()
      .then(setPresets)
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!compact || !accordionOpen) return;

    const handlePointerDown = (event: MouseEvent) => {
      const target = event.target as Node | null;
      if (!target) return;
      const inside =
        accordionAnchorRef.current?.contains(target) || accordionPanelRef.current?.contains(target);
      if (!inside) setAccordionOpen(false);
    };

    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, [accordionOpen, compact]);

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
      <div className="td-deck-settings-accordion" ref={accordionAnchorRef}>
        <button
          type="button"
          className="td-deck-settings-accordion__summary"
          aria-expanded={accordionOpen}
          aria-haspopup="dialog"
          onClick={() => setAccordionOpen((prev) => !prev)}
        >
          Templates e temas
        </button>
        <AnchoredPanelPortal
          open={accordionOpen}
          anchorRef={accordionAnchorRef}
          panelRef={accordionPanelRef}
          variant="bare"
          className="td-deck-settings-accordion__body td-deck-settings-accordion__body--portal"
          role="dialog"
          aria-label="Templates e temas"
        >
          {body}
        </AnchoredPanelPortal>
      </div>
    );
  }

  return body;
}
