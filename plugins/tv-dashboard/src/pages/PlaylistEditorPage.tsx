import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  Copy,
  Eye,
  Link2,
  Plus,
  QrCode,
  RefreshCw,
  Trash2,
} from "lucide-react";

import {
  activatePlaylist,
  addSlide,
  deactivatePlaylist,
  deletePlaylist,
  deleteSlide,
  duplicateSlide,
  downloadQrPng,
  getPlaylist,
  getPreviewPayload,
  listNativeScreens,
  regeneratePlaylistToken,
  reorderSlides,
  updatePlaylist,
  type NativeScreenCatalogItem,
  type Playlist,
  type PresentationPayload,
  type Slide,
} from "../api/tvDashboardApi";
import { AddSlideModal } from "../components/AddSlideModal";
import { PresentationPreview } from "../presentation/PresentationPreview";

type Props = {
  playlistId: string;
  onBack: () => void;
};

const VIEWPORT_OPTIONS = [
  { value: "1080p", label: "1920×1080 (Full HD)" },
  { value: "1080p_portrait", label: "1080×1920 (Retrato)" },
  { value: "4k", label: "3840×2160 (4K)" },
  { value: "720p", label: "1280×720 (HD)" },
];

const TRANSITION_OPTIONS = [
  { value: "fade", label: "Fade" },
  { value: "slide", label: "Deslizar" },
  { value: "none", label: "Sem transição" },
];

export function PlaylistEditorPage({ playlistId, onBack }: Props) {
  const [playlist, setPlaylist] = useState<Playlist | null>(null);
  const [catalog, setCatalog] = useState<NativeScreenCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewPayload, setPreviewPayload] = useState<PresentationPayload | null>(null);
  const [addModalOpen, setAddModalOpen] = useState(false);

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

  async function handleAddNative(payload: {
    screenKey: string;
    title: string;
    nativeConfig: Record<string, unknown>;
    durationSec: number;
  }) {
    if (!playlist) return;
    const slide = await addSlide(playlist.id, {
      slideType: "native",
      title: payload.title,
      nativeScreenKey: payload.screenKey,
      nativeConfig: payload.nativeConfig,
      durationSec: payload.durationSec,
    });
    setPlaylist({ ...playlist, slides: [...(playlist.slides ?? []), slide] });
  }

  async function handleAddExternal(payload: {
    title: string;
    externalUrl: string;
    durationSec: number;
  }) {
    if (!playlist) return;
    const slide = await addSlide(playlist.id, {
      slideType: "external",
      title: payload.title,
      externalUrl: payload.externalUrl,
      durationSec: payload.durationSec,
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

  async function moveSlide(slide: Slide, direction: -1 | 1) {
    if (!playlist) return;
    const slides = [...(playlist.slides ?? [])].sort((a, b) => a.sortOrder - b.sortOrder);
    const index = slides.findIndex((item) => item.id === slide.id);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= slides.length) return;
    const reordered = [...slides];
    [reordered[index], reordered[target]] = [reordered[target], reordered[index]];
    const items = reordered.map((item, sortOrder) => ({ id: item.id, sortOrder }));
    const result = await reorderSlides(playlist.id, items);
    setPlaylist({ ...playlist, slides: result.slides });
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

  async function handleRegenerateToken() {
    if (!playlist) return;
    if (
      !window.confirm(
        "Gerar novo link? TVs com o link atual deixarão de funcionar até usar o novo endereço.",
      )
    ) {
      return;
    }
    const updated = await regeneratePlaylistToken(playlist.id);
    setPlaylist({ ...updated, slides: playlist.slides });
    window.alert("Novo link gerado.");
  }

  async function handleDuplicateSlide(slide: Slide) {
    if (!playlist) return;
    const copy = await duplicateSlide(playlist.id, slide.id);
    setPlaylist({ ...playlist, slides: [...(playlist.slides ?? []), copy] });
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

  function openQr() {
    void downloadQrPng(playlistId).then((blob) => {
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener,noreferrer");
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
    }).catch((err) => {
      window.alert(err instanceof Error ? err.message : "Erro ao gerar QR.");
    });
  }

  const slides = useMemo(
    () => [...(playlist?.slides ?? [])].sort((a, b) => a.sortOrder - b.sortOrder),
    [playlist?.slides],
  );

  if (loading) return <div className="td-state">Carregando programação…</div>;
  if (error || !playlist) return <div className="td-state">{error ?? "Programação não encontrada."}</div>;

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
          <button type="button" className="td-btn" onClick={openQr}>
            <QrCode size={16} />
            QR code
          </button>
          <button type="button" className="td-btn" onClick={() => void handleRegenerateToken()}>
            <RefreshCw size={16} />
            Novo link
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
          <p className="td-subtitle" style={{ marginTop: 0 }}>
            {playlist.viewCount ?? 0} visualizações
            {playlist.lastPresentedAt
              ? ` · última exibição ${new Date(playlist.lastPresentedAt).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })}`
              : ""}
            {playlist.isActive ? "" : " · link inativo"}
          </p>
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
            <label htmlFor="td-transition">Transição</label>
            <select
              id="td-transition"
              value={playlist.transitionStyle}
              onChange={(e) => void saveSettings("transitionStyle", e.target.value)}
            >
              {TRANSITION_OPTIONS.map((opt) => (
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
            <button type="button" className="td-btn td-btn--primary" onClick={() => setAddModalOpen(true)}>
              <Plus size={16} />
              Adicionar tela
            </button>
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
                  <div className="td-slide-actions">
                    <button type="button" className="td-btn td-btn--icon" disabled={idx === 0} onClick={() => void moveSlide(slide, -1)} aria-label="Mover para cima">
                      <ArrowUp size={14} />
                    </button>
                    <button type="button" className="td-btn td-btn--icon" disabled={idx === slides.length - 1} onClick={() => void moveSlide(slide, 1)} aria-label="Mover para baixo">
                      <ArrowDown size={14} />
                    </button>
                    <button type="button" className="td-btn td-btn--icon" onClick={() => void handleDuplicateSlide(slide)} aria-label="Duplicar tela">
                      <Copy size={14} />
                    </button>
                    <button type="button" className="td-btn td-btn--danger td-btn--icon" onClick={() => void handleRemoveSlide(slide)} aria-label="Remover">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <AddSlideModal
        open={addModalOpen}
        catalog={catalog}
        onClose={() => setAddModalOpen(false)}
        onAddNative={(payload) => void handleAddNative(payload)}
        onAddExternal={(payload) => void handleAddExternal(payload)}
      />

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
