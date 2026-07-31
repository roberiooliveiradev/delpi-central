import { lazy, Suspense, type ReactNode } from "react";

import type { AppPublicPages } from "../../shell/types";
import { PublicLoadingSplash } from "../../shell/PublicLoadingSplash";
import { fetchPublicPresentation, type PublicPresentationPayload } from "./api";

/** Lazy: evita puxar tv-dashboard-presentation no boot de SIPAT/CX/Kaizen. */
const PresentationView = lazy(() =>
  import("./PresentationView").then((mod) => ({ default: mod.PresentationView })),
);

function LazyPresentation({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <Suspense fallback={<PublicLoadingSplash chrome="kiosk" label="Carregando apresentação" />}>
      {children}
    </Suspense>
  );
}

export const tvDashboardPages: AppPublicPages = {
  present: {
    documentTitle: "Painéis TV — DELPI",
    chrome: "kiosk",
    notFoundTitle: "Programação indisponível",
    notFoundMessage: "Esta programação não está disponível ou foi desativada.",
    load: ({ token }) => fetchPublicPresentation(token),
    render: (data, ctx) => (
      <LazyPresentation>
        <PresentationView
          payload={data as PublicPresentationPayload}
          token={ctx.token}
          mode="public"
        />
      </LazyPresentation>
    ),
  },
};
