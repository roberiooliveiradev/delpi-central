import type { AppPublicPages } from "../../shell/types";
import { fetchPublicSipatSurvey, type PublicSipatSurvey } from "./api";
import { SipatFormPage } from "./SipatFormPage";

export const cipaPages: AppPublicPages = {
  sipat: {
    documentTitle: "Pesquisa SIPAT — CIPA · DELPI",
    chrome: "fullpage",
    notFoundMessage: "Esta pesquisa SIPAT não está disponível.",
    load: ({ token }) => fetchPublicSipatSurvey(token),
    render: (data, ctx) => (
      <SipatFormPage survey={data as PublicSipatSurvey} token={ctx.token} />
    ),
  },
};
