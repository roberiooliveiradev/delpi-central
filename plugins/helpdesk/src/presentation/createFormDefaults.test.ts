import { describe, expect, it } from "vitest";

import {
  GLPI_DEFAULT_IMPACT_ID,
  GLPI_DEFAULT_TYPE_ID,
  GLPI_DEFAULT_URGENCY_ID,
  pickCatalogDefault,
} from "./createFormDefaults";

const items = [
  { id: 5, name: "Alta" },
  { id: 3, name: "Média" },
  { id: 1, name: "Baixa" },
];

describe("pickCatalogDefault", () => {
  it("nunca usa a primeira linha do catálogo quando não há default canônico", () => {
    expect(pickCatalogDefault(items, "", undefined, null)).toBe("");
  });

  it("aplica o default canônico GLPI quando presente no catálogo", () => {
    expect(pickCatalogDefault(items, "", undefined, 3)).toBe("3");
  });

  it("ignora default canônico ausente do catálogo", () => {
    expect(pickCatalogDefault(items, "", undefined, 99)).toBe("");
  });

  it("restaura o valor do rascunho quando válido", () => {
    expect(pickCatalogDefault(items, "", "5", 3)).toBe("5");
  });

  it("descarta valor de rascunho fora do catálogo", () => {
    expect(pickCatalogDefault(items, "", "77", 3)).toBe("3");
  });

  it("preserva a seleção corrente do usuário", () => {
    expect(pickCatalogDefault(items, "1", "5", 3)).toBe("1");
  });

  it("defaults GLPI documentados são os canônicos", () => {
    expect(GLPI_DEFAULT_URGENCY_ID).toBe(3);
    expect(GLPI_DEFAULT_IMPACT_ID).toBe(3);
    expect(GLPI_DEFAULT_TYPE_ID).toBe(1);
  });
});
