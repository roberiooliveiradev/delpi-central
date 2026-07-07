import { useEffect, useState, type ReactNode } from "react";
import { LayoutTemplate, MousePointer2, Settings2 } from "lucide-react";
import { FieldLabel, TabHintCell } from "@delpi/plugin-ui";

import type { BranchScope, NativeScreenCatalogItem, Playlist, Slide } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DeckInspectorLayout } from "./deck";
import { BranchField } from "./BranchField";

type TabId = "element" | "slide" | "playlist";

type Props = {
  playlist: Playlist;
  slide: Slide | null;
  catalog: NativeScreenCatalogItem[];
  branchScope: BranchScope | null;
  showElementTab?: boolean;
  elementTab?: ReactNode;
  slideTabExtra?: ReactNode;
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

const TAB_META: Record<TabId, { label: string; hint: string; icon: typeof LayoutTemplate }> = {
  element: {
    label: "Elemento",
    hint: TV_DASHBOARD_HELP_TOOLTIPS.tabs.element,
    icon: MousePointer2,
  },
  slide: {
    label: "Tela",
    hint: TV_DASHBOARD_HELP_TOOLTIPS.tabs.slide,
    icon: LayoutTemplate,
  },
  playlist: {
    label: "Programação",
    hint: TV_DASHBOARD_HELP_TOOLTIPS.tabs.playlist,
    icon: Settings2,
  },
};

const F = TV_DASHBOARD_HELP_TOOLTIPS.fields;

export function DeckSettingsTabs({
  playlist,
  slide,
  catalog,
  branchScope,
  showElementTab = false,
  elementTab,
  slideTabExtra,
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

  const tabs: Array<{ id: TabId; disabled?: boolean }> = [
    ...(showElementTab ? [{ id: "element" as const }] : []),
    { id: "slide", disabled: !slide },
    { id: "playlist" },
  ];

  return (
    <section className="td-deck-tabs" aria-label="Configurações">
      <div className="td-deck-tabs__nav" role="tablist">
        {tabs.map((tab) => {
          const meta = TAB_META[tab.id];
          return (
            <TabHintCell
              key={tab.id}
              label={meta.label}
              hint={meta.hint}
              icon={meta.icon}
              active={activeTab === tab.id}
              disabled={tab.disabled}
              onSelect={() => setActiveTab(tab.id)}
              cellClassName="td-deck-tabs__tab-cell"
              tabClassName="td-deck-tabs__tab"
              tabActiveClassName="td-deck-tabs__tab--active"
            />
          );
        })}
      </div>

      <div className="td-deck-tabs__panel" role="tabpanel">
        {activeTab === "element" && showElementTab ? elementTab : null}

        {activeTab === "slide" && slide ? (
          <>
            <div className="td-deck-tabs__grid">
            <div className="td-field">
              <FieldLabel htmlFor="td-slide-title" label="Título" hint={F.slideTitle} className="td-field__label" />
              <input
                id="td-slide-title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                onBlur={() => saveSlidePatch({ title })}
              />
            </div>
            <div className="td-field">
              <FieldLabel htmlFor="td-slide-duration" label="Duração (s)" hint={F.slideDuration} className="td-field__label" />
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
                <FieldLabel htmlFor="td-slide-url" label="URL (https://)" hint={F.slideUrl} className="td-field__label" />
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
                  hint={F.slideBranch}
                  scope={branchScope}
                  value={branch}
                  onChange={(value) => {
                    setBranch(value);
                    saveSlidePatch({ branch: value });
                  }}
                />
                <div className="td-field">
                  <FieldLabel htmlFor="td-slide-period" label="Período (dias)" hint={F.slidePeriod} className="td-field__label" />
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
                hint={F.slideBranch}
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
            {slideTabExtra ? <DeckInspectorLayout>{slideTabExtra}</DeckInspectorLayout> : null}
          </>
        ) : null}

        {activeTab === "slide" && !slide ? (
          <p className="td-subtitle">Selecione uma tela para editar propriedades.</p>
        ) : null}

        {activeTab === "playlist" ? (
          <div className="td-deck-tabs__grid">
            <div className="td-field">
              <FieldLabel htmlFor="td-viewport" label="Resolução alvo" hint={F.viewport} className="td-field__label" />
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
              <FieldLabel htmlFor="td-transition" label="Transição" hint={F.transition} className="td-field__label" />
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
              <FieldLabel htmlFor="td-duration-default" label="Duração padrão (s)" hint={F.defaultDuration} className="td-field__label" />
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
              <FieldLabel htmlFor="td-refresh" label="Atualizar dados a cada (s)" hint={F.refreshInterval} className="td-field__label" />
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
              <FieldLabel htmlFor="td-public-url" label="Link público" hint={F.publicUrl} className="td-field__label" />
              <input id="td-public-url" readOnly value={playlist.publicUrl ?? ""} />
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
