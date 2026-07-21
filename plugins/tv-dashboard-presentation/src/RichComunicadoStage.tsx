import type { CSSProperties, ReactNode } from "react";
import { useMemo } from "react";

import { comunicadoBackgroundCssProperties } from "./comunicadoBackgroundStyle";
import { ComunicadoBlockView } from "./comunicadoBlockView";
import { useComunicadoCustomFonts } from "./comunicadoCustomFonts";
import { useComunicadoGoogleFonts } from "./comunicadoGoogleFonts";
import {
  parseComunicadoConfig,
  sortBlocksByZIndex,
  type ComunicadoScreenDataLike,
} from "./comunicadoHelpers";
import { filterBlocksVisibleOnStage } from "./comunicadoStageVisibility";
import type { ComunicadoBackground, ComunicadoBlock } from "./comunicadoTypes";
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
};

/**
 * Palco canônico do slide personalizado (fundo + logo master + blocos).
 * Editor e TV/prévia consomem este componente — sem segunda árvore de markup.
 */
export function RichComunicadoStage({
  data,
  fontScale = 1,
  inputsInteractive = false,
  inputRuntimeValues,
  onInputValueChange,
  renderBlock,
  className = "tdp-native-screen tdp-comunicado",
  stageClassName = "tdp-comunicado__stage",
  masterLogoClassName = "tdp-comunicado__master-logo",
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
      } as Record<string, unknown>),
    [data],
  );

  useComunicadoGoogleFonts({ blocks: normalized.blocks });
  useComunicadoCustomFonts(normalized.customFonts ?? (data.customFonts as never));

  const master = data.master?.enabled ? data.master : null;
  const slideBackground = normalized.background ?? data.background;
  const background =
    slideBackground ??
    master?.background ??
    ({ type: "color", value: "#ffffff" } as ComunicadoBackground);
  const imageUrl =
    background.type === "image" ? background.url ?? background.value : undefined;
  const bgStyle: CSSProperties = comunicadoBackgroundCssProperties(background, imageUrl);

  const blocks = filterBlocksVisibleOnStage(sortBlocksByZIndex(normalized.blocks ?? []));
  const logo = master?.logo;

  return (
    <div className={className} style={bgStyle}>
      <div className={stageClassName}>
        <RichComunicadoMasterLogo
          url={logo?.url}
          frame={logo?.frame}
          opacity={logo?.opacity ?? 1}
          className={masterLogoClassName}
        />
        {blocks.map((block) =>
          renderBlock ? (
            <div key={block.id}>{renderBlock(block)}</div>
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
            />
          ),
        )}
      </div>
    </div>
  );
}
