import type { AppPublicPages } from "../../shell/types";
import { CanalDenunciaPublicForm } from "./DenunciaPage";

/** Token estático do link compartilhado: /p/canal-denuncia/denuncia/aberto */
export const CANAL_DENUNCIA_PUBLIC_TOKEN = "aberto";

export const canalDenunciaPages: AppPublicPages = {
  denuncia: {
    documentTitle: "Canal de Denúncia — DELPI",
    chrome: "fullpage",
    notFoundMessage: "Este formulário de denúncia não está disponível.",
    load: async ({ token }) => {
      if (token !== CANAL_DENUNCIA_PUBLIC_TOKEN) {
        return null;
      }
      return { ok: true };
    },
    render: () => <CanalDenunciaPublicForm />,
  },
};
