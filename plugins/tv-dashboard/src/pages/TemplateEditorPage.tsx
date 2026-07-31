import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft } from "lucide-react";

import {
  getSlideTemplate,
  publishSlideTemplate,
  updateSlideTemplate,
  type SlideTemplate,
} from "../api/tvDashboardApi";
import { HttpRequestError } from "../api/httpClient";
import { ComunicadoComposerField } from "../components/ComunicadoComposerField";
import {
  clearTemplateDraft,
  resolveTemplateConfigWithLocalDraft,
  writeTemplateDraft,
} from "../utils/templateDraftPreferences";
import { tvDashboardNotice } from "../utils/tvDashboardNotice";

type Props = {
  templateId: string;
  canManage: boolean;
  onBack: () => void;
};

const AUTOSAVE_MS = 800;

export function TemplateEditorPage({ templateId, canManage, onBack }: Props) {
  const [template, setTemplate] = useState<SlideTemplate | null>(null);
  const [config, setConfig] = useState<Record<string, unknown>>({});
  const [version, setVersion] = useState(1);
  const [status, setStatus] = useState<string>("draft");
  const [label, setLabel] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);
  const versionRef = useRef(1);
  const configRef = useRef<Record<string, unknown>>({});

  versionRef.current = version;
  configRef.current = config;

  const load = useCallback(async () => {
    if (!canManage) {
      setLoading(false);
      setError("Você não tem permissão para editar templates.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const item = await getSlideTemplate(templateId);
      const resolved = resolveTemplateConfigWithLocalDraft(
        templateId,
        item.nativeConfig ?? {},
        item.version,
      );
      setTemplate(item);
      setLabel(item.label);
      setStatus(item.status);
      setVersion(item.version);
      setConfig(resolved.nativeConfig);
      if (resolved.fromDraft) {
        tvDashboardNotice("Rascunho local restaurado após F5.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar template.");
    } finally {
      setLoading(false);
    }
  }, [canManage, templateId]);

  useEffect(() => {
    void load();
  }, [load]);

  const persist = useCallback(
    async (nextConfig: Record<string, unknown>, nextLabel?: string) => {
      setSaving(true);
      try {
        const updated = await updateSlideTemplate(templateId, {
          version: versionRef.current,
          nativeConfig: nextConfig,
          label: nextLabel ?? label,
        });
        setVersion(updated.version);
        setStatus(updated.status);
        setTemplate(updated);
        writeTemplateDraft(templateId, nextConfig, updated.version);
      } catch (err) {
        if (err instanceof HttpRequestError && err.status === 409) {
          tvDashboardNotice("Conflito de versão — recarregando template.");
          await load();
        } else {
          tvDashboardNotice(err instanceof Error ? err.message : "Erro ao salvar.");
        }
      } finally {
        setSaving(false);
      }
    },
    [label, load, templateId],
  );

  const onChange = useCallback(
    (next: Record<string, unknown>) => {
      setConfig(next);
      writeTemplateDraft(templateId, next, versionRef.current);
      if (timerRef.current) window.clearTimeout(timerRef.current);
      timerRef.current = window.setTimeout(() => {
        void persist(next);
      }, AUTOSAVE_MS);
    },
    [persist, templateId],
  );

  useEffect(() => {
    return () => {
      if (timerRef.current) window.clearTimeout(timerRef.current);
    };
  }, []);

  async function handlePublish() {
    if (timerRef.current) {
      window.clearTimeout(timerRef.current);
      await persist(configRef.current);
    }
    try {
      const published = await publishSlideTemplate(templateId);
      setStatus(published.status);
      setVersion(published.version);
      clearTemplateDraft(templateId);
      tvDashboardNotice("Template publicado.");
    } catch (err) {
      tvDashboardNotice(err instanceof Error ? err.message : "Erro ao publicar.");
    }
  }

  if (!canManage) {
    return (
      <div className="td-home">
        <p className="td-state">Você não tem permissão para editar templates.</p>
        <button type="button" className="td-btn td-btn--ghost" onClick={onBack}>
          Voltar
        </button>
      </div>
    );
  }

  if (loading) return <div className="td-state">Carregando editor…</div>;
  if (error) {
    return (
      <div className="td-home">
        <p className="td-state">{error}</p>
        <button type="button" className="td-btn td-btn--ghost" onClick={onBack}>
          Voltar
        </button>
      </div>
    );
  }

  return (
    <div className="td-template-editor">
      <header className="td-template-editor__bar">
        <button type="button" className="td-btn td-btn--ghost" onClick={onBack}>
          <ArrowLeft size={16} aria-hidden="true" /> Biblioteca
        </button>
        <input
          className="td-template-editor__label"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          onBlur={() => void persist(configRef.current, label)}
          aria-label="Nome do template"
        />
        <span className="td-template-lib__badge">
          {status === "published" ? "Publicado" : status === "archived" ? "Arquivado" : "Rascunho"}
          {template?.isSystem ? " · Sistema" : ""}
          {saving ? " · Salvando…" : ""}
        </span>
        <button type="button" className="td-btn" onClick={() => void handlePublish()}>
          Publicar
        </button>
      </header>
      <ComunicadoComposerField
        playlistId="template-library"
        value={config}
        onChange={onChange}
      />
    </div>
  );
}
