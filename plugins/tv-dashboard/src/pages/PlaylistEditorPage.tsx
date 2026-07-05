import { useCallback, useEffect, useState } from "react";
import {
  ArrowLeft,
  Copy,
  Eye,
  Link2,
  Plus,
  Trash2,
} from "lucide-react";

import {
  activatePlaylist,
  addSlide,
  deactivatePlaylist,
  deletePlaylist,
  deleteSlide,
  getPlaylist,
  getPreviewPayload,
  listNativeScreens,
  updatePlaylist,
  type NativeScreenCatalogItem,
  type Playlist,
  type PresentationPayload,
  type Slide,
} from "../api/tvDashboardApi";
import { PresentationPreview } from "../presentation/PresentationPreview";

type Props = {
  playlistId: string;
  onBack: () => void;
};

const VIEWPORT_OPTIONS = [
  { value: "1080p", label: "1920×1080 (Full HD)" },
  { value: "4k", label: "3840×2160 (4K)" },
  { value: "720p", label: "1280×720 (HD)" },
];

export function PlaylistEditorPage({ playlistId, onBack }: Props) {
  const [playlist, setPlaylist] = useState<Playlist | null>(null);
  const [catalog, setCatalog] = useState<NativeScreenCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewPayload, setPreviewPayload] = useState<PresentationPayload | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [pl, screens] = await Promise.all([
        getPlaylist(playlistId),
        listNativeScreens(),
      ]);
      setPlaylist(pl);
      setCatalog(screens);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar programação.");
    } finally {
      setLoading(false);
    }
  }, [playlistId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function saveSettings(field: string, value: string | number) {
    if (!playlist) return;
    const updated = await updatePlaylist(playlist.id, { [field]: value });
    setPlaylist({ ...updated, slides: playlist.slides });
  }

  async function handleAddNative() {
    if (!playlist || !catalog.length) return;
    const screen = catalog[0];
    const title = window.prompt("Título da tela:", screen.label) ?? screen.label;
    const slide = await addSlide(playlist.id, {
      slideType: "native",
      title,
      nativeScreenKey: screen.key,
      nativeConfig: screen.key === "custom_message"
        ? { headline: "Comunicado", subtitle: "" }
        : { periodDays: 7 },
      durationSec: screen.defaultDurationSec,
    });
    setPlaylist({ ...playlist, slides: [...(playlist.slides ?? []), slide] });
  }

  async function handleAddExternal() {
    if (!playlist) return;
    const url = window.prompt("URL externa (https://):");
    if (!url?.trim()) return;
    const title = window.prompt("Título da tela:", "Link externo") ?? "Link externo";
    const slide = await addSlide(playlist.id, {
      slideType: "external",
      title,
      externalUrl: url.trim(),
      durationSec: 30,
    });
    setPlaylist({ ...playlist, slides: [...(playlist.slides ?? []), slide] });
  }

  async function handleRemoveSlide(slide: Slide) {
    if (!playlist) return;
    if (!window.confirm(`Remover a tela «${slide.title}»?`)) return;
    await deleteSlide(playlist.id, slide.id);
    setPlaylist({
      ...playlist,
      slides: (playlist.slides ?? []).filter((item) => item.id !== slide.id),
    });
  }

  async function handleToggleActive() {
    if (!playlist) return;
    const updated = playlist.isActive
      ? await deactivatePlaylist(playlist.id)
      : await activatePlaylist(playlist.id);
    setPlaylist({ ...updated, slides: playlist.slides });
  }

  async function handleDelete() {
    if (!playlist) return;
    if (!window.confirm("Excluir esta programação permanentemente?")) return;
    await deletePlaylist(playlist.id);
    onBack();
  }

  async function openPreview() {
    const payload = await getPreviewPayload(playlistId);
    setPreviewPayload(payload);
    setPreviewOpen(true);
  }

  function copyLink() {
    if (!playlist?.publicUrl) return;
    void navigator.clipboard.writeText(playlist.publicUrl);
    window.alert("Link copiado.");
  }

  if (loading) return <div className="td-state">Carregando programação…</div>;
  if (error || !playlist) return <div className="td-state">{error ?? "Programação não encontrada."}</div>;

  const slides = [...(playlist.slides ?? [])].sort((a, b) => a.sortOrder - b.sortOrder);

  return (
    <>
      <div className="td-toolbar">
        <button type="button" className="td-btn" onClick={onBack}>
          <ArrowLeft size={16} />
          Voltar
        </button>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button type="button" className="td-btn" onClick={() => void openPreview()}>
            <Eye size={16} />
            Pré-visualizar
          </button>
          <button type="button" className="td-btn" onClick={copyLink}>
            <Copy size={16} />
            Copiar link
          </button>
          <button type="button" className="td-btn" onClick={() => void handleToggleActive()}>
            <Link2 size={16} />
            {playlist.isActive ? "Desativar link" : "Reativar link"}
          </button>
          <button type="button" className="td-btn td-btn--danger" onClick={() => void handleDelete()}>
            <Trash2 size={16} />
            Excluir
          </button>
        </div>
      </div>

      <div className="td-grid-2">
        <div className="td-card">
          <h2 style={{ marginTop: 0 }}>{playlist.name}</h2>
          <div className="td-field">
            <label htmlFor="td-viewport">Resolução alvo</label>
            <select
              id="td-viewport"
              value={playlist.viewportProfile}
              onChange={(e) => void saveSettings("viewportProfile", e.target.value)}
            >
              {VIEWPORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div className="td-field">
            <label htmlFor="td-duration">Duração padrão (s)</label>
            <input
              id="td-duration"
              type="number"
              min={5}
              max={600}
              value={playlist.defaultDurationSec}
              onChange={(e) => void saveSettings("defaultDurationSec", Number(e.target.value))}
            />
          </div>
          <div className="td-field">
            <label htmlFor="td-refresh">Atualizar dados a cada (s)</label>
            <input
              id="td-refresh"
              type="number"
              min={30}
              max={3600}
              value={playlist.globalRefreshSec}
              onChange={(e) => void saveSettings("globalRefreshSec", Number(e.target.value))}
            />
          </div>
          <div className="td-link-box">
            <input readOnly value={playlist.publicUrl ?? ""} aria-label="Link público" />
          </div>
        </div>

        <div className="td-card">
          <div className="td-toolbar" style={{ marginBottom: 0 }}>
            <h3 style={{ margin: 0 }}>Telas ({slides.length})</h3>
            <div style={{ display: "flex", gap: 8 }}>
              <button type="button" className="td-btn" onClick={() => void handleAddNative()}>
                <Plus size={16} />
                Nativa
              </button>
              <button type="button" className="td-btn" onClick={() => void handleAddExternal()}>
                <Plus size={16} />
                Externa
              </button>
            </div>
          </div>
          <div className="td-slide-list">
            {slides.length === 0 ? (
              <p className="td-subtitle">Adicione telas nativas DELPI ou links externos (Power BI, sites).</p>
            ) : (
              slides.map((slide, idx) => (
                <div key={slide.id} className="td-slide-item">
                  <strong>{idx + 1}</strong>
                  <div>
                    <div>{slide.title}</div>
                    <div className="td-slide-meta">
                      {slide.slideType === "native"
                        ? `Nativa · ${slide.nativeScreenKey}`
                        : `Externa · ${slide.externalUrl}`}
                      {" · "}
                      {slide.durationSec ?? playlist.defaultDurationSec}s
                    </div>
                  </div>
                  <button type="button" className="td-btn td-btn--danger" onClick={() => void handleRemoveSlide(slide)}>
                    <Trash2 size={14} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {previewOpen && previewPayload ? (
        <div className="td-preview-frame">
          <button type="button" className="td-btn td-preview-close" onClick={() => setPreviewOpen(false)}>
            Fechar preview
          </button>
          <PresentationPreview
            payload={previewPayload}
            onRefresh={() => getPreviewPayload(playlistId)}
          />
        </div>
      ) : null}
    </>
  );
}
