import { describe, expect, it } from "vitest";

import { CM_HELP } from "../content/helpTooltips";
import {
  PROPOSALS_DOCUMENTS_COLUMN_HELP,
  withColumnHelp,
} from "./customersColumnHelp";

describe("Data da proposta (GLPI #1321)", () => {
  it("informa a proveniência ADY_DATA e não a confunde com última alteração", () => {
    const description = CM_HELP.proposals.columns.data;
    expect(description).toContain("ADY_DATA");
    expect(description).toContain("Não representa a última alteração");
    expect(description).toContain("revisões");
  });

  it("exibe a ajuda no cabeçalho da coluna data, sem mudar a chave de ordenação", () => {
    const columns = withColumnHelp(
      [{ key: "data", header: "Data da proposta", sortable: true }],
      PROPOSALS_DOCUMENTS_COLUMN_HELP,
    );
    expect(columns).toEqual([
      {
        key: "data",
        header: "Data da proposta",
        sortable: true,
        headerHint: CM_HELP.proposals.columns.data,
      },
    ]);
  });
});
