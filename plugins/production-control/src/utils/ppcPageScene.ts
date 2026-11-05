import type { CSSProperties } from "react";

import pcpFactoryBackgroundUrl from "../assets/background/background_pcp_fabrica_desfocada_4k.webp";

/** Classe CSS do fundo fotográfico seletivo do PCP (não global no shell). */
export const PPC_PAGE_SCENE_CLASS = "ppc-page-scene";

export function ppcPageSceneStyle(): CSSProperties {
  return {
    ["--ppc-page-scene-image" as string]: `url(${JSON.stringify(pcpFactoryBackgroundUrl)})`,
  };
}
