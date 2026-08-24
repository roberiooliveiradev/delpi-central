import { useEffect, useRef, useState, type ReactNode } from "react";
import { NativeCheckboxControl, TransitionGallery } from "@delpi/plugin-ui/index";
import {
  formatPresentationTransitionLabel,
  PRESENTATION_TRANSITION_STYLES,
  type PresentationTransitionStyle,
} from "@delpi/tv-dashboard-presentation";
import {
  ArrowLeftRight,
  Building2,
  Clock,
  Copy,
  Filter,
  FolderOpen,
  Globe,
  Layers,
  LayoutTemplate,
  Link2,
  Monitor,
  RefreshCw,
  Trash2,
  Type,
  Upload,
} from "lucide-react";

import type {
  BranchScope,
  NativeScreenCatalogItem,
  Playlist,
  PlaylistMasterConfig,
  PlaylistSection,
  Slide,
} from "../api/tvDashboardApi";
import { adminMediaUrl, uploadPlaylistMedia } from "../api/tvDashboardApi";
import { validateMediaUploadFile } from "../api/mediaUploadLimits";
import { useAuthenticatedBlobUrl } from "../hooks/useAuthenticatedBlobUrl";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  applySlideBatchPatch,
  buildSparseSlidePatch,
  isNativeOperationalSlide,
  resolveMixedSlideField,
  slideBatchFieldApplicability,
  type SlideBatchInput,
} from "../utils/applySlideBatchPatch";
import {
  resolveSlideDurationSec,
  slideDurationIsOverride,
} from "../utils/slideTimingInheritance";
import { tvDashboardNotice } from "../utils/tvDashboardNotice";
import { BranchField } from "./BranchField";
import type { DeckRibbonTabId } from "./deck/deckRibbonTabMeta";
import { DeckRangeField } from "./deck/DeckRangeField";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";
import { DeckRibbonTilePopover } from "./deck/DeckRibbonTilePopover";
import { PlaylistDataFiltersFields } from "./PlaylistDataFiltersFields";
import { TdNativeTextField } from "./tdFormFields";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";
import { ViewportResolutionFields } from "./ViewportResolutionFields";
import { useOptionalComunicadoEditor } from "./comunicadoEditorContext";
import { MediaLibraryModal } from "./MediaLibraryModal";

type Props = {
  activeTab: Extract<DeckRibbonTabId, "slide" | "playlist">;
  playlist: Playlist;
  slide: Slide | null;
  /** Todas as telas — schema dos filtros globais. */
  slides?: Slide[];
  sections?: PlaylistSection[];
  catalog: NativeScreenCatalogItem[];
  branchScope: BranchScope | null;
  slideTabExtra?: ReactNode;
  /** Telas do filmstrip na ordem da seleção (último = primária). */
  selectedSlides?: Slide[];
  onSavePlaylistSettings: (field: string, value: string | number | Record<string, unknown>) => void;
  onSaveSlide: (
    slide: Slide,
    payload: {
      title: string;
      durationSec: number | null;
      nativeConfig?: Record<string, unknown>;
      externalUrl?: string;
      transitionStyle?: string | null;
    },
  ) => void;
  onSaveSlides?: (slides: Slide[], patch: SlideBatchInput) => void;
};

const F = TV_DASHBOARD_HELP_TOOLTIPS.fields;
const R = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

const TRANSITION_OPTIONS = PRESENTATION_TRANSITION_STYLES.map((id) => ({
  id,
  label: formatPresentationTransitionLabel(id),
  description: F.transitionDescriptions[id as PresentationTransitionStyle],
}));

const SLIDE_TRANSITION_OPTIONS = [
  {
    id: "",
    label: F.transitionInheritLabel,
    description: F.transitionInheritDescription,
    previewStyle: "fade",
  },
  ...TRANSITION_OPTIONS,
];

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
  slides: slidesProp,
  sections = [],
  catalog,
  branchScope,
  slideTabExtra,
  selectedSlides: selectedSlidesProp,
  onSavePlaylistSettings,
  onSaveSlide,
  onSaveSlides,
}: Props) {
  const editor = useOptionalComunicadoEditor();
  const [playlistLibraryOpen, setPlaylistLibraryOpen] = useState(false);
  const slides = slidesProp ?? playlist.slides ?? [];
  const selectedSlides =
    selectedSlidesProp && selectedSlidesProp.length > 0
      ? selectedSlidesProp
      : slide
        ? [slide]
        : [];
  const [title, setTitle] = useState("");
  const [titleMixed, setTitleMixed] = useState(false);
  const [durationSec, setDurationSec] = useState(playlist.defaultDurationSec);
  const [durationInherit, setDurationInherit] = useState(true);
  const [durationInheritMixed, setDurationInheritMixed] = useState(false);
  const [transitionStyle, setTransitionStyle] = useState("");
  const [transitionMixed, setTransitionMixed] = useState(false);
  const [externalUrl, setExternalUrl] = useState("");
  const [externalUrlMixed, setExternalUrlMixed] = useState(false);
  const [branch, setBranch] = useState("");
  const [branchMixed, setBranchMixed] = useState(false);
  const [periodDays, setPeriodDays] = useState(30);
  const [periodMixed, setPeriodMixed] = useState(false);
  const [masterUploading, setMasterUploading] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);
  const logoInputRef = useRef<HTMLInputElement>(null);
  const bgInputRef = useRef<HTMLInputElement>(null);

  const slideSection = slide?.sectionId
    ? sections.find((section) => section.id === slide.sectionId)
    : undefined;
  const inheritedDuration = resolveSlideDurationSec({
    slideDuration: null,
    sectionDefault: slideSection?.defaultDurationSec,
    playlistDefault: playlist.defaultDurationSec,
  });
  const effectiveDuration = durationInherit ? inheritedDuration : durationSec;
  const fieldApplicability = slideBatchFieldApplicability(selectedSlides);
  const mixedLabel = F.mixedValue;
  const showPeriod = selectedSlides.some(
    (item) => isNativeOperationalSlide(item) && item.nativeScreenKey !== "supplies_stock_value",
  );
  const typeKey = resolveMixedSlideField(
    selectedSlides.map((item) => item.nativeScreenKey ?? item.slideType),
  );

  useEffect(() => {
    if (selectedSlides.length === 0) return;
    const titles = resolveMixedSlideField(selectedSlides.map((item) => item.title));
    setTitleMixed(titles.mixed);
    setTitle(titles.mixed ? "" : (titles.value ?? ""));

    const inheritFlags = selectedSlides.map((item) => !slideDurationIsOverride(item.durationSec));
    const inheritState = resolveMixedSlideField(inheritFlags);
    setDurationInheritMixed(inheritState.mixed);
    setDurationInherit(!inheritState.mixed && Boolean(inheritState.value));

    const durationValues = selectedSlides.map((item) =>
      resolveSlideDurationSec({
        slideDuration: item.durationSec,
        sectionDefault: item.sectionId
          ? sections.find((section) => section.id === item.sectionId)?.defaultDurationSec
          : null,
        playlistDefault: playlist.defaultDurationSec,
      }),
    );
    const durationState = resolveMixedSlideField(durationValues);
    setDurationSec(
      durationState.mixed
        ? playlist.defaultDurationSec
        : (durationState.value ?? playlist.defaultDurationSec),
    );

    const transitions = resolveMixedSlideField(
      selectedSlides.map((item) => item.transitionStyle ?? ""),
    );
    setTransitionMixed(transitions.mixed);
    setTransitionStyle(transitions.mixed ? "" : (transitions.value ?? ""));

    const urls = resolveMixedSlideField(selectedSlides.map((item) => item.externalUrl ?? ""));
    setExternalUrlMixed(urls.mixed);
    setExternalUrl(urls.mixed ? "" : (urls.value ?? ""));

    const branches = resolveMixedSlideField(
      selectedSlides.map((item) => String(item.nativeConfig?.branch ?? "")),
    );
    setBranchMixed(branches.mixed);
    setBranch(branches.mixed ? "" : (branches.value ?? ""));

    const periods = resolveMixedSlideField(
      selectedSlides.map((item) => Number(item.nativeConfig?.periodDays ?? 30)),
    );
    setPeriodMixed(periods.mixed);
    setPeriodDays(periods.mixed ? 30 : (periods.value ?? 30));
  }, [selectedSlides, playlist.defaultDurationSec, sections]);

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
  const { src: logoPreviewSrc } = useAuthenticatedBlobUrl(logoUrl);

  function saveMaster(next: PlaylistMasterConfig) {
    onSavePlaylistSettings("masterConfig", next);
  }

  async function uploadMasterAsset(kind: "logo" | "background", file: File) {
    const validationError = validateMediaUploadFile(file, ["image"]);
    if (validationError) {
      tvDashboardNotice(validationError);
      return;
    }
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
      durationSec: number | null;
      durationInherit: boolean;
      externalUrl: string;
      branch: string;
      periodDays: number;
      transitionStyle: string;
    }>,
  ) {
    if (selectedSlides.length === 0) return;
    const input = buildSparseSlidePatch(patch);
    if (Object.keys(input).length === 0) return;
    if (onSaveSlides) {
      onSaveSlides(selectedSlides, input);
      return;
    }
    if (!slide) return;
    const applied = applySlideBatchPatch([slide], input).applied[0];
    if (!applied) return;
    onSaveSlide(slide, {
      title: applied.payload.title ?? slide.title,
      durationSec:
        applied.payload.durationSec !== undefined
          ? applied.payload.durationSec
          : (slide.durationSec ?? null),
      nativeConfig: applied.payload.nativeConfig,
      externalUrl: applied.payload.externalUrl,
      transitionStyle: applied.payload.transitionStyle,
    });
  }

  if (activeTab === "slide" && selectedSlides.length === 0) {
    return <p className="td-subtitle">Selecione uma tela para editar propriedades.</p>;
  }

  if (activeTab === "slide" && selectedSlides.length > 0) {
    return (
      <>
        <DeckRibbonGroup groupId="slide-properties" label="Propriedades" hint={F.slideTitle}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
            <DeckRibbonTilePopover
              icon={Type}
              label="Título"
              hint={F.slideTitle}
              panelLabel="Título da tela"
              panelClassName="td-deck-ribbon-tile-popover--narrow"
            >
              <TdNativeTextField
                id="td-slide-title"
                label="Título"
                value={title}
                placeholder={titleMixed ? mixedLabel : undefined}
                onChange={(value) => {
                  setTitle(value);
                  setTitleMixed(false);
                }}
                onBlur={() => {
                  if (titleMixed && !title.trim()) return;
                  saveSlidePatch({ title });
                }}
              />
            </DeckRibbonTilePopover>

            <DeckRibbonTilePopover
              icon={Clock}
              label="Duração"
              hint={F.slideDuration}
              panelLabel="Duração da tela"
              panelClassName="td-deck-ribbon-tile-popover--timing"
            >
              <div className="td-deck-slide-timing">
                <NativeCheckboxControl
                  id="td-slide-duration-inherit"
                  checked={durationInherit && !durationInheritMixed}
                  label={durationInheritMixed ? `Herdar duração (${mixedLabel})` : "Herdar duração"}
                  onChange={(checked) => {
                    setDurationInherit(checked);
                    setDurationInheritMixed(false);
                    if (checked) {
                      setDurationSec(effectiveDuration);
                      saveSlidePatch({ durationInherit: true, durationSec: null });
                      return;
                    }
                    setDurationSec(effectiveDuration);
                    saveSlidePatch({
                      durationInherit: false,
                      durationSec: effectiveDuration,
                    });
                  }}
                />
                {durationInherit && !durationInheritMixed ? (
                  <p className="td-deck-slide-timing__inherited" aria-live="polite">
                    Efetivo: <strong>{effectiveDuration}s</strong>
                    <span className="td-deck-slide-timing__badge">Herdado</span>
                  </p>
                ) : (
                  <DeckRangeField
                    id="td-slide-duration-range"
                    label="Segundos"
                    hint={F.slideDuration}
                    min={5}
                    max={600}
                    value={durationSec}
                    onChange={(value) => {
                      setDurationSec(value);
                      setDurationInherit(false);
                      setDurationInheritMixed(false);
                      saveSlidePatch({ durationInherit: false, durationSec: value });
                    }}
                  />
                )}
              </div>
            </DeckRibbonTilePopover>

            <DeckRibbonTilePopover
              icon={ArrowLeftRight}
              label="Transição"
              hint={F.slideTransition}
              panelLabel="Transição da tela"
              panelClassName="td-deck-ribbon-tile-popover--transition"
            >
              <TransitionGallery
                ariaLabel="Transição do slide"
                value={transitionMixed ? null : transitionStyle}
                onChange={(value: string) => {
                  setTransitionStyle(value);
                  setTransitionMixed(false);
                  saveSlidePatch({ transitionStyle: value });
                }}
                options={SLIDE_TRANSITION_OPTIONS}
              />
            </DeckRibbonTilePopover>

            {fieldApplicability.externalUrl ? (
              <DeckRibbonTilePopover
                icon={Globe}
                label="URL"
                hint={F.slideUrl}
                panelLabel="URL externa"
                panelClassName="td-deck-ribbon-tile-popover--wide"
              >
                <TdNativeTextField
                  id="td-slide-url"
                  label="URL"
                  className="td-deck-tabs__field--wide"
                  value={externalUrl}
                  placeholder={externalUrlMixed ? mixedLabel : undefined}
                  onChange={(value) => {
                    setExternalUrl(value);
                    setExternalUrlMixed(false);
                  }}
                  onBlur={() => {
                    if (externalUrlMixed && !externalUrl.trim()) return;
                    saveSlidePatch({ externalUrl });
                  }}
                />
              </DeckRibbonTilePopover>
            ) : null}
            {fieldApplicability.branch ? (
              <DeckRibbonTilePopover
                icon={Building2}
                label="Filial"
                hint={F.slideBranch}
                panelLabel="Filial da tela"
                panelClassName="td-deck-ribbon-tile-popover--narrow"
              >
                <BranchField
                  id="td-slide-branch"
                  label="Filial"
                  scope={branchScope}
                  value={branch}
                  diverged={branchMixed}
                  divergedLabel={mixedLabel}
                  onChange={(value) => {
                    setBranch(value);
                    setBranchMixed(false);
                    saveSlidePatch({ branch: value });
                  }}
                />
              </DeckRibbonTilePopover>
            ) : null}
            {showPeriod ? (
              <DeckRibbonTilePopover
                icon={Clock}
                label="Período"
                hint={F.slidePeriod}
                panelLabel="Período em dias"
                panelClassName="td-deck-ribbon-tile-popover--narrow"
              >
                <DeckRangeField
                  id="td-slide-period"
                  label={periodMixed ? `Período (dias) — ${mixedLabel}` : "Período (dias)"}
                  hint={F.slidePeriod}
                  min={1}
                  max={365}
                  value={periodDays}
                  onChange={(value) => {
                    setPeriodDays(value);
                    setPeriodMixed(false);
                    saveSlidePatch({ periodDays: value });
                  }}
                />
              </DeckRibbonTilePopover>
            ) : null}
          </div>
        </DeckRibbonGroup>
        {!typeKey.mixed && (isCustomSlide || catalogItem) ? (
          <DeckRibbonGroup groupId="slide-type" label="Tipo" hint={F.customSlideType}>
            <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
              <DeckRibbonTile
                icon={LayoutTemplate}
                label={isCustomSlide ? "Livre" : (catalogItem?.label ?? "Tipo")}
                hint={isCustomSlide ? F.customSlideType : `Tipo: ${catalogItem?.label}`}
                disabled
                onClick={() => undefined}
              />
            </div>
          </DeckRibbonGroup>
        ) : null}
        {slideTabExtra ? (
          <DeckRibbonGroup groupId="slide-tools" label="Ferramentas">
            <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-settings-tools-row">
              {slideTabExtra}
            </div>
          </DeckRibbonGroup>
        ) : null}
      </>
    );
  }

  function openPlaylistMediaLibrary() {
    if (editor) {
      editor.openMediaLibrary("playlist");
      return;
    }
    setPlaylistLibraryOpen(true);
  }

  if (activeTab === "playlist") {
    return (
      <>
        <DeckRibbonGroup groupId="playlist-rotation" label="Rotação" hint={F.viewport}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
            <DeckRibbonTilePopover
              icon={Monitor}
              label="Resolução"
              hint={F.viewport}
              panelLabel="Resolução alvo"
              panelClassName="td-deck-ribbon-tile-popover--wide td-deck-ribbon-tile-popover--viewport"
            >
              <ViewportResolutionFields
                compact
                value={{
                  viewportProfile: playlist.viewportProfile,
                  viewportWidth: playlist.viewportWidth,
                  viewportHeight: playlist.viewportHeight,
                }}
                onChange={(next) => onSavePlaylistSettings("viewport", next)}
              />
            </DeckRibbonTilePopover>

            <DeckRibbonTilePopover
              icon={ArrowLeftRight}
              label="Transição"
              hint={F.transition}
              panelLabel="Transição da programação"
              panelClassName="td-deck-ribbon-tile-popover--transition"
            >
              <TransitionGallery
                ariaLabel="Transição da programação"
                value={playlist.transitionStyle}
                options={TRANSITION_OPTIONS}
                onChange={(value) => onSavePlaylistSettings("transitionStyle", value)}
              />
            </DeckRibbonTilePopover>

            <DeckRibbonTilePopover
              icon={Clock}
              label="Duração"
              hint={F.defaultDuration}
              panelLabel="Duração padrão"
              panelClassName="td-deck-ribbon-tile-popover--timing"
            >
              <DeckRangeField
                id="td-duration-default"
                label="Duração padrão (s)"
                hint={F.defaultDuration}
                min={5}
                max={600}
                value={playlist.defaultDurationSec}
                onChange={(value) => onSavePlaylistSettings("defaultDurationSec", value)}
              />
            </DeckRibbonTilePopover>

            <DeckRibbonTilePopover
              icon={RefreshCw}
              label="Atualizar"
              hint={F.refreshInterval}
              panelLabel="Atualizar dados na TV"
              panelClassName="td-deck-ribbon-tile-popover--timing"
            >
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
            </DeckRibbonTilePopover>
          </div>
        </DeckRibbonGroup>

        <DeckRibbonGroup groupId="playlist-media" label="Mídia" hint={R.mediaLibrary}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
            <DeckRibbonTile
              icon={FolderOpen}
              label="Biblioteca"
              hint={R.mediaLibrary}
              onClick={openPlaylistMediaLibrary}
            />
          </div>
        </DeckRibbonGroup>

        <DeckRibbonGroup groupId="playlist-filters" label="Filtros" hint={R.playlistFilters}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
            <DeckRibbonTilePopover
              icon={Filter}
              label="Filtros"
              hint={F.dataDefaults}
              panelLabel="Filtros da programação"
              panelClassName="td-deck-ribbon-tile-popover--wide td-deck-ribbon-tile-popover--filters"
            >
              <PlaylistDataFiltersFields
                slides={slides}
                values={playlist.dataDefaults}
                branchScope={branchScope}
                onChange={(next) => onSavePlaylistSettings("dataDefaults", next)}
              />
            </DeckRibbonTilePopover>
          </div>
        </DeckRibbonGroup>

        <DeckRibbonGroup groupId="playlist-link" label="Link público" hint={F.publicUrl}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
            <DeckRibbonTilePopover
              icon={Link2}
              label="URL"
              hint={F.publicUrl}
              panelLabel="Link público da TV"
              panelClassName="td-deck-ribbon-tile-popover--wide"
            >
              <TdNativeTextField
                id="td-public-url"
                label="URL"
                hint={F.publicUrl}
                value={playlist.publicUrl ?? ""}
                onChange={() => undefined}
                readOnly
              />
            </DeckRibbonTilePopover>
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
          groupId="playlist-master"
          label="Master"
          hint="Fundo e logo compartilhados quando o slide não define o próprio fundo (4E.3)."
        >
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
            <DeckRibbonTilePopover
              icon={Layers}
              label="Master"
              hint="Fundo e logo compartilhados nas telas livres."
              panelLabel="Master slide"
              panelClassName="td-deck-ribbon-tile-popover--master"
            >
              <div className="td-deck-master td-deck-master--popover">
                <NativeCheckboxControl
                  className="td-deck-master__toggle"
                  label="Ativo em telas livres"
                  checked={masterEnabled}
                  onChange={(enabled) => saveMaster(patchMaster(master, { enabled }))}
                />
                <div className="td-deck-master__row td-deck-master__row--dense">
                  <TvRibbonColorPicker
                    label="Fundo"
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
                    label="Imagem"
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
                      label="Remover"
                      onClick={() => saveMaster(patchMaster(master, { logo: undefined }))}
                    />
                  ) : null}
                </div>
                {logoUrl ? (
                  <div
                    className="td-deck-master__logo-preview"
                    style={
                      logoPreviewSrc
                        ? { backgroundImage: `url(${logoPreviewSrc})` }
                        : undefined
                    }
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
            </DeckRibbonTilePopover>
          </div>
        </DeckRibbonGroup>
        {!editor && playlistLibraryOpen ? (
          <MediaLibraryModal
            open={playlistLibraryOpen}
            target="playlist"
            playlistId={playlist.id}
            uploading={false}
            onClose={() => setPlaylistLibraryOpen(false)}
            onPick={() => setPlaylistLibraryOpen(false)}
            onUploaded={() => undefined}
          />
        ) : null}
      </>
    );
  }

  return null;
}
