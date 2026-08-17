import { describe, expect, it } from "vitest";

import { EMPTY_QUERY } from "../types/thirdPartyMaterials";
import { buildUrlSearch, parseUrlState, queryFromUrlState } from "./urlState";

describe("urlState", () => {
  it("parseia filtros e recno da remessa", () => {
    const state = parseUrlState(
      "?branch=01&product=10211413&customerReference=10018137&status=partial&onlyWithBalance=true&shipment=27062725",
    );
    expect(state.branch).toBe("01");
    expect(state.product).toBe("10211413");
    expect(state.customerReference).toBe("10018137");
    expect(state.status).toBe("partial");
    expect(state.onlyWithBalance).toBe(true);
    expect(state.shipmentRecno).toBe("27062725");
  });

  it("ignora status inválido", () => {
    expect(parseUrlState("?status=PARCIAL").status).toBe("");
  });

  it("serializa só campos preenchidos", () => {
    const search = buildUrlSearch({
      ...EMPTY_QUERY,
      branch: "01",
      product: "10211413",
      customerReference: "10018137",
      onlyWithBalance: true,
      shipmentRecno: "99",
    });
    expect(search).toBe(
      "?branch=01&product=10211413&customerReference=10018137&onlyWithBalance=true&shipment=99",
    );
  });

  it("separa query da remessa selecionada", () => {
    const query = queryFromUrlState({
      ...EMPTY_QUERY,
      branch: "02",
      shipmentRecno: "1",
    });
    expect(query.branch).toBe("02");
    expect("shipmentRecno" in query).toBe(false);
  });
});
