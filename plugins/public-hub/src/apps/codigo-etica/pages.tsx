import type { AppPublicPages } from "../../shell/types";
import { CodigoEticaPublicView } from "./CodigoPage";

/** Token estático do link compartilhado: /p/codigo-etica/codigo/aberto */
export const CODIGO_ETICA_PUBLIC_TOKEN = "aberto";

export const codigoEticaPages: AppPublicPages = {
  codigo: {
    documentTitle: "Código de Ética — DELPI",
    chrome: "fullpage",
    notFoundMessage: "Este documento não está disponível.",
    load: async ({ token }) => {
      if (token !== CODIGO_ETICA_PUBLIC_TOKEN) {
        return null;
      }
      return { ok: true };
    },
    render: () => <CodigoEticaPublicView />,
  },
};
