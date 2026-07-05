import type { AppPublicPages } from "../../shell/types";
import { fetchPublicPresentation, type PublicPresentationPayload } from "./api";
import { PresentationView } from "./PresentationView";

export const tvDashboardPages: AppPublicPages = {
  present: {
    documentTitle: "Painéis TV — DELPI",
    chrome: "kiosk",
    notFoundMessage: "Esta programação não está disponível ou foi desativada.",
    load: ({ token }) => fetchPublicPresentation(token),
    render: (data, ctx) => (
      <PresentationView
        payload={data as PublicPresentationPayload}
        token={ctx.token}
        mode="public"
      />
    ),
  },
};
