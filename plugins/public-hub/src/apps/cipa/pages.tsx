import type { AppPublicPages } from "../../shell/types";
import { fetchPublicSipatSurvey, type PublicSipatSurvey } from "./api";
import { fetchPublicSignContext } from "./signApi";
import { SipatFormPage } from "./SipatFormPage";
import { CipaSignPage } from "./SignPage";

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
  sign: {
    documentTitle: "Assinar ata — CIPA · DELPI",
    chrome: "fullpage",
    notFoundMessage: "Este link de assinatura não está disponível ou expirou.",
    load: ({ token }) => fetchPublicSignContext(token),
    render: (data, ctx) => (
      <CipaSignPage context={data as import("./signApi").PublicSignContext} token={ctx.token} />
    ),
  },
};
