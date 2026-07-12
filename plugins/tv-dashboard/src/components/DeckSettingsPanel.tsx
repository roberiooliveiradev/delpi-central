import { useEffect, useRef, useState } from "react";
import {
  ArrowLeftRight,
  Building2,
  CalendarRange,
  Globe,
  Image as ImageIcon,
  LayoutTemplate,
  Timer,
  Type,
  Upload,
} from "lucide-react";

import type {
  BranchScope,
  NativeScreenCatalogItem,
  Playlist,
  PlaylistMasterConfig,
  Slide,
} from "../api/tvDashboardApi";
import { adminMediaUrl, uploadPlaylistMedia } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { BranchField } from "./BranchField";
import type { DeckRibbonTabId } from "./deck/deckRibbonTabMeta";
import { DeckIconField } from "./deck/DeckIconField";
import { TdNativeSelectField, TdNativeTextField } from "./tdFormFields";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";

type Props = {
  activeTab: Extract<DeckRibbonTabId, "slide" | "playlist">;
  playlist: Playlist;
  slide: Slide | null;
  catalog: NativeScreenCatalogItem[];
  branchScope: BranchScope | null;
  slideTabExtra?: React.ReactNode;
  onSavePlaylistSettings: (field: string, value: string | number | Record<string, unknown>) => void;
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

function patchMaster(
  current: PlaylistMasterConfig | undefined,
  patch: Partial<PlaylistMasterConfig>,
): PlaylistMasterConfig {
  return {
    ...(current ?? {}),
    ...patch,
  };
}

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
  const [masterUploading, setMasterUploading] = useState(false);
  const logoInputRef = useRef<HTMLInputElement>(null);
  const bgInputRef = useRef<HTMLInputElement>(null);

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
  const master = playlist.masterConfig ?? {};
  const masterEnabled = Boolean(master.enabled);
  const masterBgColor =
    master.background?.type === "color" ? (master.background.value ?? "#0f172a") : "#0f172a";
  const logoUrl =
    master.logo?.url ??
    (master.logo?.assetId ? adminMediaUrl(playlist.id, master.logo.assetId) : undefined);

  function saveMaster(next: PlaylistMasterConfig) {
    onSavePlaylistSettings("masterConfig", next);
  }

  async function uploadMasterAsset(kind: "logo" | "background", file: File) {
    setMasterUploading(true);
    try {
      const asset = await uploadPlaylistMedia(playlist.id, file);
      const url = adminMediaUrl(playlist.id, asset.id);
      if (kind === "logo") {
        saveMaster(
          patchMaster(master, {
            enabled: true,
            logo: { assetId: asset.id, url, frame: master.logo?.frame ?? { x: 2, y: 2, w: 12, h: 10 } },
          }),
        );
      } else {
        saveMaster(
          patchMaster(master, {
            enabled: true,
            background: { type: "image", assetId: asset.id, url },
          }),
        );
      }
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "Falha no upload.");
    } finally {
      setMasterUploading(false);
    }
  }

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
      <div className="td-deck-settings-strip td-deck-settings-strip--slide">
        <div className="td-deck-tabs__grid td-deck-tabs__grid--icon-fields">
          <DeckIconField id="td-slide-title" icon={Type} label="Título" hint={F.slideTitle}>
            <TdNativeTextField
              id="td-slide-title"
              label=""
              value={title}
              onChange={setTitle}
              onBlur={() => saveSlidePatch({ title })}
            />
          </DeckIconField>
          <DeckIconField
            id="td-slide-duration"
            icon={Timer}
            label="Duração"
            hint={F.slideDuration}
            className="td-deck-icon-field--narrow"
          >
            <TdNativeTextField
              id="td-slide-duration"
              label=""
              type="number"
              min={5}
              max={600}
              value={String(durationSec)}
              onChange={(value) => setDurationSec(Number(value))}
              onBlur={() => saveSlidePatch({ durationSec })}
            />
          </DeckIconField>
          <DeckIconField
            id="td-slide-transition"
            icon={ArrowLeftRight}
            label="Transição"
            hint={F.slideTransition}
            className="td-deck-icon-field--medium"
          >
            <TdNativeSelectField
              id="td-slide-transition"
              label=""
              value={transitionStyle}
              onChange={(value) => {
                setTransitionStyle(value);
                saveSlidePatch({ transitionStyle: value });
              }}
              options={SLIDE_TRANSITION_OPTIONS}
            />
          </DeckIconField>
          {slide.slideType === "external" ? (
            <DeckIconField
              id="td-slide-url"
              icon={Globe}
              label="URL"
              hint={F.slideUrl}
              className="td-deck-icon-field--wide"
            >
              <TdNativeTextField
                id="td-slide-url"
                label=""
                className="td-deck-tabs__field--wide"
                value={externalUrl}
                onChange={setExternalUrl}
                onBlur={() => saveSlidePatch({ externalUrl })}
              />
            </DeckIconField>
          ) : !isCustomSlide && slide.nativeScreenKey !== "supplies_stock_value" ? (
            <>
              <DeckIconField icon={Building2} label="Filial" hint={F.slideBranch}>
                <BranchField
                  id="td-slide-branch"
                  label=""
                  scope={branchScope}
                  value={branch}
                  onChange={(value) => {
                    setBranch(value);
                    saveSlidePatch({ branch: value });
                  }}
                />
              </DeckIconField>
              <DeckIconField
                id="td-slide-period"
                icon={CalendarRange}
                label="Período"
                hint={F.slidePeriod}
                className="td-deck-icon-field--narrow"
              >
                <TdNativeTextField
                  id="td-slide-period"
                  label=""
                  type="number"
                  min={1}
                  max={365}
                  value={String(periodDays)}
                  onChange={(value) => setPeriodDays(Number(value))}
                  onBlur={() => saveSlidePatch({ periodDays })}
                />
              </DeckIconField>
            </>
          ) : !isCustomSlide ? (
            <DeckIconField icon={Building2} label="Filial" hint={F.slideBranch}>
              <BranchField
                id="td-slide-branch-stock"
                label=""
                scope={branchScope}
                value={branch}
                onChange={(value) => {
                  setBranch(value);
                  saveSlidePatch({ branch: value });
                }}
              />
            </DeckIconField>
          ) : null}
          {isCustomSlide ? (
            <span className="td-deck-settings-chip" title={F.customSlideType}>
              <LayoutTemplate size={13} aria-hidden="true" />
              Tela livre
            </span>
          ) : catalogItem ? (
            <span className="td-deck-settings-chip" title={`Tipo: ${catalogItem.label}`}>
              <LayoutTemplate size={13} aria-hidden="true" />
              {catalogItem.label}
            </span>
          ) : null}
        </div>
        {slideTabExtra ? <div className="td-deck-settings-strip__tools">{slideTabExtra}</div> : null}
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

        <div className="td-deck-master">
          <div className="td-deck-master__header">
            <ImageIcon size={14} aria-hidden="true" />
            <strong>Master slide</strong>
            <label className="td-deck-master__toggle">
              <input
                type="checkbox"
                checked={masterEnabled}
                onChange={(event) =>
                  saveMaster(patchMaster(master, { enabled: event.target.checked }))
                }
              />
              Ativo em telas livres
            </label>
          </div>
          <p className="td-subtitle">
            Fundo e logo compartilhados quando o slide não define o próprio fundo (4E.3).
          </p>
          <div className="td-deck-master__row">
            <TvRibbonColorPicker
              label="Fundo sólido"
              value={masterBgColor}
              onChange={(color) =>
                saveMaster(
                  patchMaster(master, {
                    enabled: true,
                    background: { type: "color", value: color },
                  }),
                )
              }
            />
            <button
              type="button"
              className="td-btn td-btn--sm"
              disabled={masterUploading}
              onClick={() => bgInputRef.current?.click()}
            >
              <Upload size={14} aria-hidden="true" />
              Fundo imagem
            </button>
            <button
              type="button"
              className="td-btn td-btn--sm"
              disabled={masterUploading}
              onClick={() => logoInputRef.current?.click()}
            >
              <Upload size={14} aria-hidden="true" />
              Logo
            </button>
            {logoUrl ? (
              <button
                type="button"
                className="td-btn td-btn--sm"
                onClick={() => saveMaster(patchMaster(master, { logo: undefined }))}
              >
                Remover logo
              </button>
            ) : null}
          </div>
          {logoUrl ? (
            <div
              className="td-deck-master__logo-preview"
              style={{ backgroundImage: `url(${logoUrl})` }}
              title="Logo do master"
            />
          ) : null}
          <input
            ref={logoInputRef}
            type="file"
            accept="image/*"
            hidden
            onChange={(event) => {
              const file = event.target.files?.[0];
              event.target.value = "";
              if (file) void uploadMasterAsset("logo", file);
            }}
          />
          <input
            ref={bgInputRef}
            type="file"
            accept="image/*"
            hidden
            onChange={(event) => {
              const file = event.target.files?.[0];
              event.target.value = "";
              if (file) void uploadMasterAsset("background", file);
            }}
          />
        </div>
      </div>
    );
  }

  return null;
}
