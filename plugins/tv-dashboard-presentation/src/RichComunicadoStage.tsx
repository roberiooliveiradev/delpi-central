import type {
  ComponentPropsWithRef,
  CSSProperties,
  HTMLAttributes,
  ReactNode,
} from "react";
import { Fragment, useMemo } from "react";
import {
  ComunicadoStageFrame,
  comunicadoStageBemClasses,
  ensureComunicadoDualClass,
} from "@delpi/plugin-ui/index";

import {
  comunicadoBackgroundImageUrl,
  comunicadoBackgroundRootStyle,
} from "./comunicadoBackgroundStyle";
import { ComunicadoBlockView } from "./comunicadoBlockView";
import { useComunicadoCustomFonts } from "./comunicadoCustomFonts";
import { useComunicadoGoogleFonts } from "./comunicadoGoogleFonts";
import { resolveStageMasterLogo } from "./delpiBrandLogo";
import {
  parseComunicadoConfig,
  sortBlocksByZIndex,
  type ComunicadoScreenDataLike,
} from "./comunicadoHelpers";
import { filterBlocksVisibleOnStage } from "./comunicadoStageVisibility";
import type {
  ComunicadoBackground,
  ComunicadoBlock,
  ComunicadoCustomFontRef,
} from "./comunicadoTypes";
import { RichComunicadoBackground } from "./RichComunicadoBackground";
import { RichComunicadoMasterLogo } from "./RichComunicadoMasterLogo";

export type RichComunicadoMasterPayload = {
  enabled?: boolean;
  background?: ComunicadoBackground;
  logo?: {
    url?: string;
    assetId?: string;
    frame?: { x?: number; y?: number; w?: number; h?: number };
    opacity?: number;
  };
};

export type RichComunicadoStageProps = {
  data: ComunicadoScreenDataLike & {
    background?: ComunicadoBackground;
    master?: RichComunicadoMasterPayload;
    blocks?: ComunicadoBlock[];
    customFonts?: unknown;
    dataFilters?: unknown;
    speakerNotes?: string;
    brandThemeKey?: string;
    version?: number;
  };
  fontScale?: number;
  inputsInteractive?: boolean;
  inputRuntimeValues?: Record<string, string | number | boolean | null>;
  onInputValueChange?: (blockId: string, value: string | number | boolean | null) => void;
  /**
   * Se definido, substitui o mapa padrão de `ComunicadoBlockView`
   * (ex.: chrome de seleção no editor).
   */
  renderBlock?: (block: ComunicadoBlock) => ReactNode;
  className?: string;
  stageClassName?: string;
  masterLogoClassName?: string;
  /** Estilo extra no root, aplicado sobre o estilo de fundo (editor: design size + scale). */
  style?: CSSProperties;
  /** Ref do root da moldura (editor: medições de drag). */
  rootRef?: ComponentPropsWithRef<typeof ComunicadoStageFrame>["ref"];
  /** Atributos extras do root (editor: `data-viewport`, handlers de context menu). */
  rootProps?: Omit<HTMLAttributes<HTMLDivElement>, "className" | "style" | "children"> & {
    [dataAttr: `data-${string}`]: string | number | boolean | undefined;
  };
  /**
   * Fonts já resolvidas pelo consumidor (editor: blob autenticado via Bearer).
   * Default: `normalized.customFonts` do `data`.
   */
  customFonts?: readonly ComunicadoCustomFontRef[];
  /**
   * URL da imagem de fundo já resolvida pelo consumidor (editor: blob autenticado).
   * `undefined` = resolve de `data` (default); `null` = suprime a camada.
   */
  backgroundImageUrl?: string | null;
  /**
   * URL do logo já resolvida pelo consumidor (editor: blob autenticado).
   * `undefined` = usa `resolveStageMasterLogo`; `null` = suprime o logo.
   */
  masterLogoUrl?: string | null;
  /** Conteúdo no início do `__stage`, antes de logo+blocos (editor: grade). */
  stageLeadingOverlay?: ReactNode;
  /**
   * Envolve logo+blocos dentro do `__stage` — ilha de z-index para o conteúdo
   * do slide sob overlays de interação (editor: `__stage-content`).
   */
  stageContentWrapper?: (content: ReactNode) => ReactNode;
  /** Conteúdo ao final do `__stage` (editor: guias/marquee/camada de desenho). */
  stageTrailingOverlay?: ReactNode;
};

const DEFAULT_BEM = comunicadoStageBemClasses("tdp");

/**
 * Palco canônico do slide personalizado (fundo + logo master/brand + blocos).
 * Moldura visual: `ComunicadoStageFrame` (@delpi/plugin-ui).
 * Editor e TV/prévia consomem este componente — sem segunda árvore de markup.
 */
export function RichComunicadoStage({
  data,
  fontScale = 1,
  inputsInteractive = false,
  inputRuntimeValues,
  onInputValueChange,
  renderBlock,
  className = DEFAULT_BEM.root,
  stageClassName = DEFAULT_BEM.stage,
  masterLogoClassName = DEFAULT_BEM.masterLogo,
  style,
  rootRef,
  rootProps,
  customFonts,
  backgroundImageUrl,
  masterLogoUrl,
  stageLeadingOverlay,
  stageContentWrapper,
  stageTrailingOverlay,
}: RichComunicadoStageProps) {
  const normalized = useMemo(
    () =>
      parseComunicadoConfig({
        version: data.version,
        headline: data.headline,
        subtitle: data.subtitle,
        background: data.background,
        blocks: data.blocks,
        customFonts: data.customFonts,
        dataFilters: data.dataFilters,
        speakerNotes: data.speakerNotes,
        brandThemeKey: data.brandThemeKey,
      } as Record<string, unknown>),
    [data],
  );

  useComunicadoGoogleFonts({ blocks: normalized.blocks });
  useComunicadoCustomFonts(
    customFonts ?? normalized.customFonts ?? (data.customFonts as never),
  );

  const master = data.master?.enabled ? data.master : null;
  const slideBackground = normalized.background ?? data.background;
  const background =
    slideBackground ??
    master?.background ??
    ({ type: "color", value: "#ffffff" } as ComunicadoBackground);
  const imageUrl =
    backgroundImageUrl === undefined
      ? comunicadoBackgroundImageUrl(background)
      : backgroundImageUrl;
  const bgStyle: CSSProperties = comunicadoBackgroundRootStyle(background);

  const blocks = filterBlocksVisibleOnStage(sortBlocksByZIndex(normalized.blocks ?? []));
  const logo = resolveStageMasterLogo({
    background,
    customLogo: master?.logo,
    brandThemeKey: normalized.brandThemeKey ?? (data.brandThemeKey as string | undefined),
  });
  const resolvedLogoUrl =
    masterLogoUrl === undefined ? logo?.url : masterLogoUrl;

  const stageContent = (
    <>
      {logo && resolvedLogoUrl ? (
        <RichComunicadoMasterLogo
          url={resolvedLogoUrl}
          frame={logo.frame}
          opacity={logo.opacity}
          className={ensureComunicadoDualClass(masterLogoClassName)}
        />
      ) : null}
      {blocks.map((block) =>
        renderBlock ? (
          <Fragment key={block.id}>{renderBlock(block)}</Fragment>
        ) : (
          <ComunicadoBlockView
            key={block.id}
            block={block}
            fontScale={fontScale}
            inputsInteractive={inputsInteractive}
            inputRuntimeValue={
              inputRuntimeValues && block.id in inputRuntimeValues
                ? inputRuntimeValues[block.id]
                : undefined
            }
            onInputValueChange={onInputValueChange}
            slideDataFilters={normalized.dataFilters}
            stageBlocks={normalized.blocks}
          />
        ),
      )}
    </>
  );

  return (
    <ComunicadoStageFrame
      ref={rootRef}
      className={className}
      stageClassName={stageClassName}
      style={style ? { ...bgStyle, ...style } : bgStyle}
      backgroundLayer={<RichComunicadoBackground url={imageUrl} />}
      {...rootProps}
    >
      {stageLeadingOverlay}
      {stageContentWrapper ? stageContentWrapper(stageContent) : stageContent}
      {stageTrailingOverlay}
    </ComunicadoStageFrame>
  );
}
