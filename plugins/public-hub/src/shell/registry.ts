import type { PublicRegistry } from "./types";
import { customerExperiencePages } from "../apps/customer-experience/pages";

/**
 * Registro de páginas públicas por app. Para adicionar um novo app público,
 * crie src/apps/<app>/pages.tsx exportando um AppPublicPages e registre aqui.
 */
export const publicRegistry: PublicRegistry = {
  "customer-experience": customerExperiencePages,
};
