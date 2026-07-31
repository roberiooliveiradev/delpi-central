import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  getBranchScope,
  getSlideTemplate,
  listNativeScreens,
  publishSlideTemplate,
  updateSlideTemplate,
  type BranchScope,
  type NativeScreenCatalogItem,
  type Playlist,
  type Slide,
  type SlideTemplate,
} from "../api/tvDashboardApi";
import { HttpRequestError } from "../api/httpClient";
import { CustomSlideEditorLayout } from "../components/CustomSlideEditorLayout";
import { ComunicadoEditorProvider } from "../components/comunicadoEditorContext";
import { PlaylistRenameDialog } from "../components/PlaylistRenameDialog";
import { TvDashboardScreenLoading } from "../components/TvDashboardScreenLoading";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { EditorShortcutsProvider } from "../keyboard";
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
const TEMPLATE_PLAYLIST_ID = "template-library";
const HEADER = TV_DASHBOARD_HELP_TOOLTIPS.header;

export function TemplateEditorPage({ templateId, canManage, onBack }: Props) {
  const [template, setTemplate] = useState<SlideTemplate | null>(null);
  const [config, setConfig] = useState<Record<string, unknown>>({});
  const [version, setVersion] = useState(1);
  const [status, setStatus] = useState<string>("draft");
  const [label, setLabel] = useState("");
  const [durationSec, setDurationSec] = useState<number | null>(45);
  const [catalog, setCatalog] = useState<NativeScreenCatalogItem[]>([]);
  const [branchScope, setBranchScope] = useState<BranchScope | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [renameOpen, setRenameOpen] = useState(false);
  const [renameBusy, setRenameBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);
  const versionRef = useRef(1);
  const configRef = useRef<Record<string, unknown>>({});
  const labelRef = useRef("");
  const durationRef = useRef<number | null>(45);

  versionRef.current = version;
  configRef.current = config;
  labelRef.current = label;
  durationRef.current = durationSec;

  const load = useCallback(async () => {
    if (!canManage) {
      setLoading(false);
      setError("Você não tem permissão para editar templates.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [item, screens, scope] = await Promise.all([
        getSlideTemplate(templateId),
        listNativeScreens().catch(() => [] as NativeScreenCatalogItem[]),
        getBranchScope().catch(() => null),
      ]);
      const resolved = resolveTemplateConfigWithLocalDraft(
        templateId,
        item.nativeConfig ?? {},
        item.version,
      );
      setTemplate(item);
      setLabel(item.label);
      setStatus(item.status);
      setVersion(item.version);
      setDurationSec(item.durationSec ?? 45);
      setConfig(resolved.nativeConfig);
      setCatalog(screens);
      setBranchScope(scope);
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
    async (args?: {
      nativeConfig?: Record<string, unknown>;
      label?: string;
      durationSec?: number | null;
    }) => {
      setSaving(true);
      try {
        const nextConfig = args?.nativeConfig ?? configRef.current;
        const nextLabel = args?.label ?? labelRef.current;
        const nextDuration =
          args?.durationSec !== undefined ? args.durationSec : durationRef.current;
        const updated = await updateSlideTemplate(templateId, {
          version: versionRef.current,
          nativeConfig: nextConfig,
          label: nextLabel,
          durationSec: nextDuration ?? undefined,
        });
        setVersion(updated.version);
        setStatus(updated.status);
        setTemplate(updated);
        setDurationSec(updated.durationSec ?? nextDuration);
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
    [load, templateId],
  );

  const onChange = useCallback(
    (next: Record<string, unknown>) => {
      setConfig(next);
      writeTemplateDraft(templateId, next, versionRef.current);
      if (timerRef.current) window.clearTimeout(timerRef.current);
      timerRef.current = window.setTimeout(() => {
        void persist({ nativeConfig: next });
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
      await persist();
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

  const selectedSlide: Slide = useMemo(
    () => ({
      id: templateId,
      playlistId: TEMPLATE_PLAYLIST_ID,
      sortOrder: 0,
      slideType: "native",
      title: label || "Template",
      nativeScreenKey: template?.nativeScreenKey || "custom_message",
      nativeConfig: config,
      durationSec,
      isActive: true,
    }),
    [config, durationSec, label, template?.nativeScreenKey, templateId],
  );

  const syntheticPlaylist: Playlist = useMemo(
    () => ({
      id: TEMPLATE_PLAYLIST_ID,
      publicToken: "",
      name: label || "Template",
      viewportProfile: "1080p",
      transitionStyle: "fade",
      defaultDurationSec: durationSec ?? 45,
      globalRefreshSec: 300,
      isActive: false,
      viewCount: 0,
      slides: [selectedSlide],
    }),
    [durationSec, label, selectedSlide],
  );

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

  if (loading) {
    return <TvDashboardScreenLoading label="Carregando editor…" variant="fullscreen" />;
  }
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

  const statusLabel =
    status === "published"
      ? "Publicado"
      : status === "archived"
        ? "Arquivado"
        : "Rascunho";
  const statusDetail = [
    statusLabel,
    template?.isSystem ? "Sistema" : null,
    saving ? "Salvando…" : null,
  ]
    .filter(Boolean)
    .join(" · ");

  const chromeProps = {
    playlist: syntheticPlaylist,
    slide: selectedSlide,
    catalog,
    branchScope,
    isCustomSlide: true,
    adminLabels: {},
    variant: "template" as const,
    slideDeck: {
      slides: [selectedSlide],
      selectedSlide,
      onAdd: () => undefined,
      onSelect: () => undefined,
      playlistChrome: {
        playlistName: label || "Template",
        tvStatusLabel: statusDetail,
        tvStatusClass:
          status === "published" ? "td-badge td-badge--active" : "td-badge td-badge--inactive",
        linkActive: status === "published",
        onBack,
        backLabel: HEADER.backToTemplatesLabel,
        backHint: HEADER.backToTemplates,
        headActions: (
          <button
            type="button"
            className="td-btn td-btn--primary td-deck-chrome__publish"
            title={HEADER.publishTemplate}
            onClick={() => void handlePublish()}
          >
            Publicar
          </button>
        ),
        onPreview: () => undefined,
        onShare: () => undefined,
        onCopyLink: () => undefined,
        onQr: () => undefined,
        onRegenerateToken: () => undefined,
        onToggleLink: () => undefined,
        onDelete: () => undefined,
        onRename: () => setRenameOpen(true),
      },
    },
    onSavePlaylistSettings: () => undefined,
    onSaveSlide: (
      _slide: Slide,
      payload: {
        title: string;
        durationSec: number | null;
        nativeConfig?: Record<string, unknown>;
      },
    ) => {
      if (payload.title && payload.title !== labelRef.current) {
        setLabel(payload.title);
      }
      if (payload.durationSec !== undefined) {
        setDurationSec(payload.durationSec);
      }
      if (payload.nativeConfig) {
        setConfig(payload.nativeConfig);
        writeTemplateDraft(templateId, payload.nativeConfig, versionRef.current);
      }
      void persist({
        label: payload.title || labelRef.current,
        durationSec: payload.durationSec,
        nativeConfig: payload.nativeConfig ?? configRef.current,
      });
    },
  };

  const workspaceProps = {
    slides: [selectedSlide],
    playlistId: TEMPLATE_PLAYLIST_ID,
    selectedSlideId: selectedSlide.id,
    selectedSlideIds: [selectedSlide.id],
    previewBySlideId: {},
    dragIndex: null as number | null,
    inactiveLabel: "Pausada",
    canPasteSlide: false,
    viewportProfile: "1080p",
    onSelect: () => undefined,
    onDragStart: () => undefined,
    onDrop: () => undefined,
    onDragEnd: () => undefined,
    onAdd: () => undefined,
    onCopySlide: () => undefined,
    onPasteSlide: () => undefined,
    onDuplicateSlide: () => undefined,
    onRenameSlide: () => undefined,
    onToggleSlideActive: () => undefined,
    onRemoveSlide: () => undefined,
  };

  return (
    <>
      <EditorShortcutsProvider active>
        <div className="td-deck td-deck--editor td-template-editor">
          <ComunicadoEditorProvider
            playlistId={TEMPLATE_PLAYLIST_ID}
            slideId={selectedSlide.id}
            value={config}
            onChange={onChange}
          >
            <CustomSlideEditorLayout
              variant="template"
              selectedSlide={selectedSlide}
              workspaceProps={workspaceProps}
              chromeProps={chromeProps}
              adminLabels={{}}
            />
          </ComunicadoEditorProvider>
        </div>
      </EditorShortcutsProvider>
      <PlaylistRenameDialog
        open={renameOpen}
        initialName={label}
        busy={renameBusy}
        onClose={() => {
          if (!renameBusy) setRenameOpen(false);
        }}
        onConfirm={async (name) => {
          setRenameBusy(true);
          try {
            setLabel(name);
            await persist({ label: name });
            setRenameOpen(false);
          } finally {
            setRenameBusy(false);
          }
        }}
      />
    </>
  );
}
