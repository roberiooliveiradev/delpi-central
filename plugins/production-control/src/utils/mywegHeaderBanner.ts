import type { CSSProperties } from "react";

import mywegBannerUrl from "../assets/background/banner_weg_web.webp";

/** Classe do header fotográfico exclusivo do menu Necessidades WEG / MyWEG. */
export const PPC_MYWEG_HEADER_CLASS = "ppc-header--myweg";

export function mywegHeaderBannerStyle(): CSSProperties {
  return {
    ["--ppc-myweg-header-banner" as string]: `url(${JSON.stringify(mywegBannerUrl)})`,
  };
}
