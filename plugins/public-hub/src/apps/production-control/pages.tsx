import type { AppPublicPages } from "../../shell/types";
import {
  fetchPublicDeliveryMap,
  fetchPublicMachineLoad,
  type PublicDeliveryMapPayload,
  type PublicMachineLoadPayload,
} from "./api";
import { OperatorCockpit } from "./CockpitPage";
import { DeliveryMapPublicPage } from "./DeliveryMapPublicPage";

const DEFAULT_BRANCH = "01";
const ALLOWED_BRANCHES = new Set(["01", "02"]);

function resolveBranch(): string {
  const requested = new URLSearchParams(window.location.search).get("branch")?.trim() || "";
  return ALLOWED_BRANCHES.has(requested) ? requested : DEFAULT_BRANCH;
}

function resolveSearch(): string {
  return new URLSearchParams(window.location.search).get("q")?.trim() || "";
}

type CockpitData = {
  token: string;
  branch: string;
  payload: PublicMachineLoadPayload;
};

type DeliveryMapData = {
  token: string;
  branch: string;
  payload: PublicDeliveryMapPayload;
};

export const productionControlPages: AppPublicPages = {
  cockpit: {
    documentTitle: "Fila de produção — DELPI",
    chrome: "fullpage",
    notFoundTitle: "Fila indisponível",
    notFoundMessage:
      "Este link não está ativo ou o PCP ainda não publicou a carga máquina deste período.",
    load: async ({ token }) => {
      const branch = resolveBranch();
      try {
        const payload = await fetchPublicMachineLoad(token, branch);
        return { token, branch, payload } satisfies CockpitData;
      } catch {
        return null;
      }
    },
    render: (data) => {
      const { token, branch, payload } = data as CockpitData;
      return <OperatorCockpit token={token} branch={branch} initial={payload} />;
    },
  },
  "delivery-map": {
    documentTitle: "Mapa de entrega — DELPI",
    chrome: "fullpage",
    notFoundTitle: "Mapa indisponível",
    notFoundMessage:
      "Este link não está ativo ou o PCP ainda não publicou o mapa de entrega desta filial.",
    load: async ({ token }) => {
      const branch = resolveBranch();
      const search = resolveSearch();
      try {
        const payload = await fetchPublicDeliveryMap(token, branch, search);
        return { token, branch, payload } satisfies DeliveryMapData;
      } catch {
        return null;
      }
    },
    render: (data) => {
      const { token, branch, payload } = data as DeliveryMapData;
      return <DeliveryMapPublicPage token={token} branch={branch} initial={payload} />;
    },
  },
};
