import type { AppPublicPages } from "../../shell/types";
import { fetchPublicMachineLoad, type PublicMachineLoadPayload } from "./api";
import { OperatorCockpit } from "./CockpitPage";

const DEFAULT_BRANCH = "01";
const ALLOWED_BRANCHES = new Set(["01", "02"]);

function resolveBranch(): string {
  const requested = new URLSearchParams(window.location.search).get("branch")?.trim() || "";
  return ALLOWED_BRANCHES.has(requested) ? requested : DEFAULT_BRANCH;
}

type CockpitData = {
  token: string;
  branch: string;
  payload: PublicMachineLoadPayload;
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
};
