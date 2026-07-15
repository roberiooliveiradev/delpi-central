import type { AppPublicPages } from "../../shell/types";
import { KaizenSuggestionForm } from "./SuggestionPage";

/** Token estático do link compartilhado: /p/kaizen/sugestao/aberto */
export const KAIZEN_PUBLIC_SUGGESTION_TOKEN = "aberto";

export const kaizenPages: AppPublicPages = {
  sugestao: {
    documentTitle: "Sugestão de melhorias Kaizen — DELPI",
    chrome: "fullpage",
    notFoundMessage: "Este formulário de sugestão não está disponível.",
    load: async ({ token }) => {
      if (token !== KAIZEN_PUBLIC_SUGGESTION_TOKEN) {
        return null;
      }
      return { ok: true };
    },
    render: () => <KaizenSuggestionForm />,
  },
};
