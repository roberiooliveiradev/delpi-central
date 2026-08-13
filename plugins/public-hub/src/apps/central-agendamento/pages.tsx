import type { AppPublicPages } from "../../shell/types";
import { fetchPublicSchedulingResource } from "./api";
import { PublicBookingForm } from "./BookPage";

export const centralAgendamentoPages: AppPublicPages = {
  book: {
    documentTitle: "Agendamento público — DELPI",
    chrome: "fullpage",
    notFoundTitle: "Agendamento indisponível",
    notFoundMessage: "Este link de agendamento é inválido ou foi desativado.",
    load: async ({ token }) => {
      try {
        const resource = await fetchPublicSchedulingResource(token);
        return { token, resource };
      } catch {
        return null;
      }
    },
    render: (data) => {
      const payload = data as {
        token: string;
        resource: Parameters<typeof PublicBookingForm>[0]["resource"];
      };
      return <PublicBookingForm token={payload.token} resource={payload.resource} />;
    },
  },
};
