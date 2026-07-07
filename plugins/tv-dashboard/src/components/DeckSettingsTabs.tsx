import { useEffect, useState, type ReactNode } from "react";

import type { BranchScope, NativeScreenCatalogItem, Playlist, Slide } from "../api/tvDashboardApi";
import { BranchField } from "./BranchField";

type TabId = "element" | "slide" | "playlist";

type Props = {
  playlist: Playlist;
  slide: Slide | null;
  catalog: NativeScreenCatalogItem[];
  branchScope: BranchScope | null;
  showElementTab?: boolean;
  elementTab?: ReactNode;
  selectedElementId?: string | null;
  onSavePlaylistSettings: (field: string, value: string | number) => void;
  onSaveSlide: (
    slide: Slide,
    payload: {
      title: string;
      durationSec: number;
      nativeConfig?: Record<string, unknown>;
      externalUrl?: string;
    },
  ) => void;
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

export function DeckSettingsTabs({
  playlist,
  slide,
  catalog,
  branchScope,
  showElementTab = false,
  elementTab,
  selectedElementId,
  onSavePlaylistSettings,
  onSaveSlide,
}: Props) {
  const [activeTab, setActiveTab] = useState<TabId>(showElementTab ? "element" : "slide");
  const [title, setTitle] = useState("");
  const [durationSec, setDurationSec] = useState(playlist.defaultDurationSec);
  const [externalUrl, setExternalUrl] = useState("");
  const [branch, setBranch] = useState("");
  const [periodDays, setPeriodDays] = useState(30);

  useEffect(() => {
    if (!showElementTab && activeTab === "element") {
      setActiveTab("slide");
    }
  }, [showElementTab, activeTab]);

  useEffect(() => {
    if (showElementTab && selectedElementId) {
      setActiveTab("element");
    }
  }, [showElementTab, selectedElementId]);

  useEffect(() => {
    if (!slide) return;
    setTitle(slide.title);
    setDurationSec(slide.durationSec ?? playlist.defaultDurationSec);
    setExternalUrl(slide.externalUrl ?? "");
    const cfg = slide.nativeConfig ?? {};
    setBranch(String(cfg.branch ?? ""));
    setPeriodDays(Number(cfg.periodDays ?? 30));
  }, [slide, playlist.defaultDurationSec]);

  const catalogItem = slide?.nativeScreenKey
    ? catalog.find((item) => item.key === slide.nativeScreenKey)
    : null;
  const isCustomSlide = slide?.nativeScreenKey === "custom_message";

  function saveSlidePatch(
    patch: Partial<{
      title: string;
      durationSec: number;
      externalUrl: string;
      branch: string;
      periodDays: number;
    }> = {},
  ) {
    if (!slide) return;
    const nextTitle = patch.title ?? title;
    const nextDuration = patch.durationSec ?? durationSec;
    const nextBranch = patch.branch ?? branch;
    const nextPeriod = patch.periodDays ?? periodDays;
    if (slide.slideType === "external") {
      onSaveSlide(slide, {
        title: nextTitle.trim() || slide.title,
        durationSec: nextDuration,
        externalUrl: (patch.externalUrl ?? externalUrl).trim(),
      });
      return;
    }
    const nativeConfig: Record<string, unknown> = { ...(slide.nativeConfig ?? {}) };
    const screenKey = slide.nativeScreenKey ?? "";
    if (screenKey !== "custom_message") {
      if (nextBranch.trim()) nativeConfig.branch = nextBranch.trim();
      else delete nativeConfig.branch;
      nativeConfig.periodDays = nextPeriod;
      if (screenKey === "quality_ppm_summary") {
        nativeConfig.ppmType = slide.nativeConfig?.ppmType ?? "internal";
      }
    }
    onSaveSlide(slide, {
      title: nextTitle.trim() || slide.title,
      durationSec: nextDuration,
      nativeConfig,
    });
  }

  const tabs: Array<{ id: TabId; label: string; disabled?: boolean }> = [
    ...(showElementTab ? [{ id: "element" as const, label: "Elemento" }] : []),
    { id: "slide", label: "Tela", disabled: !slide },
    { id: "playlist", label: "Programação" },
  ];

  return (
    <section className="td-deck-tabs" aria-label="Configurações">
      <div className="td-deck-tabs__nav" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            className={`td-deck-tabs__tab${activeTab === tab.id ? " td-deck-tabs__tab--active" : ""}`}
            aria-selected={activeTab === tab.id}
            disabled={tab.disabled}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="td-deck-tabs__panel" role="tabpanel">
        {activeTab === "element" && showElementTab ? elementTab : null}

        {activeTab === "slide" && slide ? (
          <div className="td-deck-tabs__grid">
            <div className="td-field">
              <label htmlFor="td-slide-title">Título</label>
              <input
                id="td-slide-title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                onBlur={() => saveSlidePatch({ title })}
              />
            </div>
            <div className="td-field">
              <label htmlFor="td-slide-duration">Duração (s)</label>
              <input
                id="td-slide-duration"
                type="number"
                min={5}
                max={600}
                value={durationSec}
                onChange={(e) => setDurationSec(Number(e.target.value))}
                onBlur={() => saveSlidePatch({ durationSec })}
              />
            </div>
            {slide.slideType === "external" ? (
              <div className="td-field td-deck-tabs__field--wide">
                <label htmlFor="td-slide-url">URL (https://)</label>
                <input
                  id="td-slide-url"
                  value={externalUrl}
                  onChange={(e) => setExternalUrl(e.target.value)}
                  onBlur={() => saveSlidePatch({ externalUrl })}
                />
              </div>
            ) : !isCustomSlide && slide.nativeScreenKey !== "supplies_stock_value" ? (
              <>
                <BranchField
                  id="td-slide-branch"
                  label="Filial (opcional)"
                  scope={branchScope}
                  value={branch}
                  onChange={(value) => {
                    setBranch(value);
                    saveSlidePatch({ branch: value });
                  }}
                />
                <div className="td-field">
                  <label htmlFor="td-slide-period">Período (dias)</label>
                  <input
                    id="td-slide-period"
                    type="number"
                    min={1}
                    max={365}
                    value={periodDays}
                    onChange={(e) => setPeriodDays(Number(e.target.value))}
                    onBlur={() => saveSlidePatch({ periodDays })}
                  />
                </div>
              </>
            ) : !isCustomSlide ? (
              <BranchField
                id="td-slide-branch-stock"
                label="Filial (opcional)"
                scope={branchScope}
                value={branch}
                onChange={(value) => {
                  setBranch(value);
                  saveSlidePatch({ branch: value });
                }}
              />
            ) : null}
            {catalogItem ? (
              <p className="td-subtitle td-deck-tabs__meta">Tipo: {catalogItem.label}</p>
            ) : null}
          </div>
        ) : null}

        {activeTab === "slide" && !slide ? (
          <p className="td-subtitle">Selecione uma tela para editar propriedades.</p>
        ) : null}

        {activeTab === "playlist" ? (
          <div className="td-deck-tabs__grid">
            <div className="td-field">
              <label htmlFor="td-viewport">Resolução alvo</label>
              <select
                id="td-viewport"
                value={playlist.viewportProfile}
                onChange={(e) => onSavePlaylistSettings("viewportProfile", e.target.value)}
              >
                {VIEWPORT_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="td-field">
              <label htmlFor="td-transition">Transição</label>
              <select
                id="td-transition"
                value={playlist.transitionStyle}
                onChange={(e) => onSavePlaylistSettings("transitionStyle", e.target.value)}
              >
                {TRANSITION_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="td-field">
              <label htmlFor="td-duration-default">Duração padrão (s)</label>
              <input
                id="td-duration-default"
                type="number"
                min={5}
                max={600}
                value={playlist.defaultDurationSec}
                onChange={(e) => onSavePlaylistSettings("defaultDurationSec", Number(e.target.value))}
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
                onChange={(e) => onSavePlaylistSettings("globalRefreshSec", Number(e.target.value))}
              />
            </div>
            <div className="td-field td-deck-tabs__field--wide">
              <label htmlFor="td-public-url">Link público</label>
              <input id="td-public-url" readOnly value={playlist.publicUrl ?? ""} />
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
