import type { PublicRegistry } from "./types";
import { customerExperiencePages } from "../apps/customer-experience/pages";
import { qualityLabelsPages } from "../apps/quality-labels/pages";
import { tvDashboardPages } from "../apps/tv-dashboard/pages";
import { kaizenPages } from "../apps/kaizen/pages";
import { cipaPages } from "../apps/cipa/pages";
import { transformometroPages } from "../apps/transformometro/pages";
import { muralAcessosPages } from "../apps/mural-acessos/pages";

/**
 * Registro de páginas públicas por app. Para adicionar um novo app público,
 * crie src/apps/<app>/pages.tsx exportando um AppPublicPages e registre aqui.
 */
export const publicRegistry: PublicRegistry = {
  "customer-experience": customerExperiencePages,
  "quality-labels": qualityLabelsPages,
  "tv-dashboard": tvDashboardPages,
  kaizen: kaizenPages,
  cipa: cipaPages,
  transformometro: transformometroPages,
  "mural-acessos": muralAcessosPages,
};
