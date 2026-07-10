import { useEffect, useState } from "react";

import type { BranchScope, NativeScreenCatalogItem, Playlist, Slide } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { BranchField } from "./BranchField";
import type { DeckRibbonTabId } from "./deck/deckRibbonTabMeta";
import { TdNativeSelectField, TdNativeTextField } from "./tdFormFields";

type Props = {
  activeTab: Extract<DeckRibbonTabId, "slide" | "playlist">;
  playlist: Playlist;
  slide: Slide | null;
  catalog: NativeScreenCatalogItem[];
  branchScope: BranchScope | null;
  slideTabExtra?: React.ReactNode;
  onSavePlaylistSettings: (field: string, value: string | number) => void;
  onSaveSlide: (
    slide: Slide,
    payload: {
      title: string;
      durationSec: number;
      nativeConfig?: Record<string, unknown>;
      externalUrl?: string;
      transitionStyle?: string | null;
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

const SLIDE_TRANSITION_OPTIONS = [
  { value: "", label: "Herdar da programação" },
  ...TRANSITION_OPTIONS,
];

const F = TV_DASHBOARD_HELP_TOOLTIPS.fields;

export function DeckSettingsPanel({
  activeTab,
  playlist,
  slide,
  catalog,
  branchScope,
  slideTabExtra,
  onSavePlaylistSettings,
  onSaveSlide,
}: Props) {
  const [title, setTitle] = useState("");
  const [durationSec, setDurationSec] = useState(playlist.defaultDurationSec);
  const [transitionStyle, setTransitionStyle] = useState("");
  const [externalUrl, setExternalUrl] = useState("");
  const [branch, setBranch] = useState("");
  const [periodDays, setPeriodDays] = useState(30);

  useEffect(() => {
    if (!slide) return;
    setTitle(slide.title);
    setDurationSec(slide.durationSec ?? playlist.defaultDurationSec);
    setTransitionStyle(slide.transitionStyle ?? "");
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
      transitionStyle: string;
    }> = {},
  ) {
    if (!slide) return;
    const nextTitle = patch.title ?? title;
    const nextDuration = patch.durationSec ?? durationSec;
    const nextBranch = patch.branch ?? branch;
    const nextPeriod = patch.periodDays ?? periodDays;
    const nextTransition = patch.transitionStyle ?? transitionStyle;
    const transitionPayload =
      nextTransition.trim() === "" ? null : nextTransition.trim();
    if (slide.slideType === "external") {
      onSaveSlide(slide, {
        title: nextTitle.trim() || slide.title,
        durationSec: nextDuration,
        externalUrl: (patch.externalUrl ?? externalUrl).trim(),
        transitionStyle: transitionPayload,
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
      transitionStyle: transitionPayload,
    });
  }

  if (activeTab === "slide" && !slide) {
    return <p className="td-subtitle">Selecione uma tela para editar propriedades.</p>;
  }

  if (activeTab === "slide" && slide) {
    return (
      <div className="td-deck-settings-strip">
        <div className="td-deck-tabs__grid">
          <TdNativeTextField
            id="td-slide-title"
            label="Título"
            hint={F.slideTitle}
            value={title}
            onChange={setTitle}
            onBlur={() => saveSlidePatch({ title })}
          />
          <TdNativeTextField
            id="td-slide-duration"
            label="Duração (s)"
            hint={F.slideDuration}
            type="number"
            min={5}
            max={600}
            value={String(durationSec)}
            onChange={(value) => setDurationSec(Number(value))}
            onBlur={() => saveSlidePatch({ durationSec })}
          />
          <TdNativeSelectField
            id="td-slide-transition"
            label="Transição desta tela"
            hint={F.slideTransition}
            value={transitionStyle}
            onChange={(value) => {
              setTransitionStyle(value);
              saveSlidePatch({ transitionStyle: value });
            }}
            options={SLIDE_TRANSITION_OPTIONS}
          />
          {slide.slideType === "external" ? (
            <TdNativeTextField
              id="td-slide-url"
              label="URL (https://)"
              hint={F.slideUrl}
              className="td-deck-tabs__field--wide"
              value={externalUrl}
              onChange={setExternalUrl}
              onBlur={() => saveSlidePatch({ externalUrl })}
            />
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
              <TdNativeTextField
                id="td-slide-period"
                label="Período (dias)"
                hint={F.slidePeriod}
                type="number"
                min={1}
                max={365}
                value={String(periodDays)}
                onChange={(value) => setPeriodDays(Number(value))}
                onBlur={() => saveSlidePatch({ periodDays })}
              />
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
        {slideTabExtra}
      </div>
    );
  }

  if (activeTab === "playlist") {
    return (
      <div className="td-deck-settings-strip">
      <div className="td-deck-tabs__grid">
        <TdNativeSelectField
          id="td-viewport"
          label="Resolução alvo"
          hint={F.viewport}
          value={playlist.viewportProfile}
          onChange={(value) => onSavePlaylistSettings("viewportProfile", value)}
          options={VIEWPORT_OPTIONS}
        />
        <TdNativeSelectField
          id="td-transition"
          label="Transição"
          hint={F.transition}
          value={playlist.transitionStyle}
          onChange={(value) => onSavePlaylistSettings("transitionStyle", value)}
          options={TRANSITION_OPTIONS}
        />
        <TdNativeTextField
          id="td-duration-default"
          label="Duração padrão (s)"
          hint={F.defaultDuration}
          type="number"
          min={5}
          max={600}
          value={String(playlist.defaultDurationSec)}
          onChange={(value) => onSavePlaylistSettings("defaultDurationSec", Number(value))}
        />
        <TdNativeTextField
          id="td-refresh"
          label="Atualizar dados a cada (s)"
          hint={F.refreshInterval}
          type="number"
          min={30}
          max={3600}
          value={String(playlist.globalRefreshSec)}
          onChange={(value) => onSavePlaylistSettings("globalRefreshSec", Number(value))}
        />
        <TdNativeTextField
          id="td-public-url"
          label="Link público"
          hint={F.publicUrl}
          className="td-deck-tabs__field--wide"
          value={playlist.publicUrl ?? ""}
          onChange={() => undefined}
          readOnly
        />
      </div>
      </div>
    );
  }

  return null;
}
