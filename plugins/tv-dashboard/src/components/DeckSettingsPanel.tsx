import { useEffect, useRef, useState, type ReactNode } from "react";
import { NativeCheckboxControl } from "@delpi/plugin-ui/index";
import {
  ArrowLeftRight,
  Building2,
  Copy,
  Globe,
  LayoutTemplate,
  Trash2,
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
import { tvDashboardNotice } from "../utils/tvDashboardNotice";
import { BranchField } from "./BranchField";
import type { DeckRibbonTabId } from "./deck/deckRibbonTabMeta";
import { DeckIconField } from "./deck/DeckIconField";
import { DeckRangeField } from "./deck/DeckRangeField";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";
import { TdNativeSelectField, TdNativeTextField } from "./tdFormFields";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";

type Props = {
  activeTab: Extract<DeckRibbonTabId, "slide" | "playlist">;
  playlist: Playlist;
  slide: Slide | null;
  catalog: NativeScreenCatalogItem[];
  branchScope: BranchScope | null;
  slideTabExtra?: ReactNode;
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
  const [linkCopied, setLinkCopied] = useState(false);
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
      tvDashboardNotice(err instanceof Error ? err.message : "Falha no upload.");
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
      <>
        <DeckRibbonGroup groupId="slide-properties" label="Propriedades" hint={F.slideTitle}>
          <div className="td-deck-ribbon__prop-cols">
            <DeckIconField id="td-slide-title" icon={Type} label="Título" hint={F.slideTitle}>
              <TdNativeTextField
                id="td-slide-title"
                label=""
                value={title}
                onChange={setTitle}
                onBlur={() => saveSlidePatch({ title })}
              />
            </DeckIconField>
            <DeckRangeField
              id="td-slide-duration"
              label="Duração (s)"
              hint={F.slideDuration}
              min={5}
              max={600}
              value={durationSec}
              onChange={(value) => {
                setDurationSec(value);
                saveSlidePatch({ durationSec: value });
              }}
            />
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
                <DeckRangeField
                  id="td-slide-period"
                  label="Período (dias)"
                  hint={F.slidePeriod}
                  min={1}
                  max={365}
                  value={periodDays}
                  onChange={(value) => {
                    setPeriodDays(value);
                    saveSlidePatch({ periodDays: value });
                  }}
                />
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
          </div>
        </DeckRibbonGroup>
        {isCustomSlide || catalogItem ? (
          <DeckRibbonGroup label="Tipo" hint={F.customSlideType}>
            <span className="td-deck-settings-chip" title={isCustomSlide ? F.customSlideType : `Tipo: ${catalogItem?.label}`}>
              <LayoutTemplate size={13} aria-hidden="true" />
              {isCustomSlide ? "Tela livre" : catalogItem?.label}
            </span>
          </DeckRibbonGroup>
        ) : null}
        {slideTabExtra ? (
          <DeckRibbonGroup label="Ferramentas">
            <div className="td-deck-settings-strip__tools">{slideTabExtra}</div>
          </DeckRibbonGroup>
        ) : null}
      </>
    );
  }

  if (activeTab === "playlist") {
    return (
      <>
        <DeckRibbonGroup label="Rotação" hint={F.viewport}>
          <div className="td-deck-tabs__grid td-deck-tabs__grid--playlist-rotation">
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
            <DeckRangeField
              id="td-duration-default"
              label="Duração padrão (s)"
              hint={F.defaultDuration}
              min={5}
              max={600}
              value={playlist.defaultDurationSec}
              onChange={(value) => onSavePlaylistSettings("defaultDurationSec", value)}
            />
            <DeckRangeField
              id="td-refresh"
              label="Atualizar dados na TV (s)"
              hint={F.refreshInterval}
              min={30}
              max={3600}
              step={10}
              value={playlist.globalRefreshSec}
              onChange={(value) => onSavePlaylistSettings("globalRefreshSec", value)}
            />
          </div>
        </DeckRibbonGroup>

        <DeckRibbonGroup label="Link público" hint={F.publicUrl} wide>
          <div className="td-deck-playlist-link">
            <TdNativeTextField
              id="td-public-url"
              label="URL"
              hint={F.publicUrl}
              className="td-deck-playlist-link__field"
              value={playlist.publicUrl ?? ""}
              onChange={() => undefined}
              readOnly
            />
            <DeckRibbonTile
              icon={Copy}
              label={linkCopied ? "Copiado" : "Copiar"}
              hint={F.publicUrl}
              disabled={!playlist.publicUrl}
              onClick={() => {
                const url = playlist.publicUrl;
                if (!url) return;
                void navigator.clipboard.writeText(url).then(() => {
                  setLinkCopied(true);
                  window.setTimeout(() => setLinkCopied(false), 2000);
                });
              }}
            />
          </div>
        </DeckRibbonGroup>

        <DeckRibbonGroup
          label="Master slide"
          hint="Fundo e logo compartilhados quando o slide não define o próprio fundo (4E.3)."
          wide
        >
          <div className="td-deck-master td-deck-master--compact">
            <div className="td-deck-master__row td-deck-master__row--dense">
              <NativeCheckboxControl
                className="td-deck-master__toggle"
                label="Ativo em telas livres"
                checked={masterEnabled}
                onChange={(enabled) => saveMaster(patchMaster(master, { enabled }))}
              />
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
              <DeckRibbonTile
                icon={Upload}
                label="Fundo imagem"
                disabled={masterUploading}
                onClick={() => bgInputRef.current?.click()}
              />
              <DeckRibbonTile
                icon={Upload}
                label="Logo"
                disabled={masterUploading}
                onClick={() => logoInputRef.current?.click()}
              />
              {logoUrl ? (
                <DeckRibbonTile
                  icon={Trash2}
                  label="Remover logo"
                  onClick={() => saveMaster(patchMaster(master, { logo: undefined }))}
                />
              ) : null}
              {logoUrl ? (
                <div
                  className="td-deck-master__logo-preview"
                  style={{ backgroundImage: `url(${logoUrl})` }}
                  title="Logo do master"
                />
              ) : null}
            </div>
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
        </DeckRibbonGroup>
      </>
    );
  }

  return null;
}
