import type { AppPublicPages } from "../../shell/types";
import { fetchPublicInspection, type PublicInspection } from "./api";
import { InspectionView } from "./InspectionPage";

export const qualityLabelsPages: AppPublicPages = {
  inspection: {
    documentTitle: "Inspeção da Qualidade — DELPI",
    notFoundMessage: "Esta inspeção não está mais disponível.",
    load: ({ token }) => fetchPublicInspection(token),
    render: (data) => <InspectionView inspection={data as PublicInspection} />,
  },
};
