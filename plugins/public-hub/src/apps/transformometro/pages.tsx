import type { AppPublicPages } from "../../shell/types";
import { fetchPublicSignContext, type PublicSignContext } from "./api";
import { SignPage } from "./SignPage";

export const transformometroPages: AppPublicPages = {
  sign: {
    documentTitle: "Assinar ata — Transformômetro · DELPI",
    chrome: "fullpage",
    notFoundMessage: "Este link de assinatura não está disponível ou expirou.",
    load: ({ token }) => fetchPublicSignContext(token),
    render: (data, ctx) => (
      <SignPage context={data as PublicSignContext} token={ctx.token} />
    ),
  },
};
