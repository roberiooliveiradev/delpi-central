import type { AppPublicPages } from "../../shell/types";
import { fetchPublicMuralMenu, type PublicMuralMenu } from "./api";
import { MuralAcessosMenuView } from "./MenuPage";

export const muralAcessosPages: AppPublicPages = {
  menu: {
    documentTitle: "Acessos DELPI",
    chrome: "fullpage",
    notFoundMessage: "Este mural não está disponível.",
    load: async ({ token }) => fetchPublicMuralMenu(token),
    render: (data) => <MuralAcessosMenuView menu={data as PublicMuralMenu} />,
  },
};
