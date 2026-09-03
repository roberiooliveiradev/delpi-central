import { describe, expect, it } from "vitest";

import {
  flattenUserManualTermCatalog,
  USER_MANUAL_TERM_CATALOG,
} from "./userManualTermCatalog";

describe("userManualTermCatalog", () => {
  it("agrupa termos já usados na UI/helps com definição e aplicação", () => {
    expect(USER_MANUAL_TERM_CATALOG.length).toBeGreaterThanOrEqual(5);
    const entries = flattenUserManualTermCatalog();
    const terms = entries.map((item) => item.term);
    expect(new Set(terms).size).toBe(terms.length);

    for (const item of entries) {
      expect(item.term.trim().length).toBeGreaterThan(1);
      expect(item.meaning.trim().length).toBeGreaterThan(12);
      expect(item.applies.trim().length).toBeGreaterThan(3);
    }

    expect(terms).toEqual(
      expect.arrayContaining([
        "Escopo",
        "Data de entrega",
        "Incoterm",
        "EXW",
        "FOB",
        "CIF",
        "ROL",
        "FIFO",
        "Pode faturar",
        "OTD",
        "Carteira em aberto",
        "Filtro de clientes",
      ]),
    );
  });
});
