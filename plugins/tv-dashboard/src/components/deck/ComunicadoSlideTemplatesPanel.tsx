import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { Download, LayoutTemplate, Upload } from "lucide-react";
import {
  exportSlideAsTemplateMdd,
  getSlidePreset,
  importSlideTemplateMdd,
  listSlidePresets,
  type SlidePreset,
} from "../../api/tvDashboardApi";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import {
  COMUNICADO_SLIDE_THEMES,
  type ComunicadoSlideTheme,
} from "../../content/comunicadoSlideThemes";
import { DeckPropertySection } from "./DeckPropertySection";
import { DeckSettingsAccordion } from "./DeckSettingsAccordion";

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function themeSwatchLabelStyle(theme: ComunicadoSlideTheme): CSSProperties {
  const color = theme.textColor;
  const isLightText = /^#f|^#e|^#fff|white/i.test(color.trim());
  return {
    color,
    textShadow: isLightText ? "0 1px 2px rgba(0, 0, 0, 0.55)" : "none",
  };
}

export function ComunicadoSlideTemplatesPanel({ compact = false }: { compact?: boolean }) {
  const { config, applySlideTemplate, applySlideTheme } = useComunicadoEditor();
  const [presets, setPresets] = useState<SlidePreset[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [applyingKey, setApplyingKey] = useState<string | null>(null);
  const [busy, setBusy] = useState<"export" | "import" | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  async function exportCurrentAsMdd() {
    setBusy("export");
    setError(null);
    try {
      const key = `preset_comunicado_${Date.now().toString(36)}`;
      const blob = await exportSlideAsTemplateMdd({
        key,
        label: "Template do slide",
        description: "Exportado do editor — versionar em slide_templates/.",
        title: "Slide personalizado",
        durationSec: 45,
        nativeConfig: config as unknown as Record<string, unknown>,
      });
      downloadBlob(blob, `${key}.mdd`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao exportar MDD.");
    } finally {
      setBusy(null);
    }
  }

  async function onImportFile(file: File | null) {
    if (!file) return;
    setBusy("import");
    setError(null);
    try {
      const parsed = await importSlideTemplateMdd(file);
      if (parsed.nativeConfig) applySlideTemplate(parsed.nativeConfig);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao importar MDD.");
    } finally {
      setBusy(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  const body = (
    <>
      <DeckPropertySection title="Templates" hint="Substitui o conteúdo do slide pelo layout do template (.mdd)." compact={compact}>
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
        <div className="td-template-mdd-actions">
          <button
            type="button"
            className="td-template-mdd-actions__btn"
            disabled={busy !== null}
            onClick={() => void exportCurrentAsMdd()}
          >
            <Download size={14} aria-hidden="true" />
            {busy === "export" ? "Exportando…" : "Exportar MDD"}
          </button>
          <button
            type="button"
            className="td-template-mdd-actions__btn"
            disabled={busy !== null}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload size={14} aria-hidden="true" />
            {busy === "import" ? "Importando…" : "Importar MDD"}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".mdd,application/zip"
            hidden
            onChange={(event) => void onImportFile(event.target.files?.[0] ?? null)}
          />
        </div>
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
