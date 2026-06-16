import { describe, expect, it } from "vitest";

import type { ChatPresentation } from "../../../data/api/chatTypes";
import { buildCategoryFilterOptions } from "../presentationCategoryFilter";
import { buildFieldLabelsFromTableColumns } from "../presentationFieldLabels";

describe("ChatRichTable filter labels", () => {
  const columns: Extract<ChatPresentation, { type: "table" }>["columns"] = [
    { key: "level", label: "Nível" },
    { key: "parent_code", label: "Código pai" },
    { key: "parent_description", label: "Descrição pai" },
    { key: "component_code", label: "Componente" },
    { key: "description", label: "Descrição" },
    { key: "type", label: "Tipo" },
    { key: "unit", label: "Unid." },
    { key: "quantity_per", label: "Qtde por" },
    { key: "accumulated_quantity", label: "Qtd acum." },
  ];

  const rows = [
    {
      level: 1,
      parent_code: "90260882",
      parent_description: "PROTETOR TERM CABO",
      component_code: "50250258",
      description: "CONJUNTO TERMOSTATO",
      type: "PI",
      unit: "MI",
      quantity_per: "1",
      accumulated_quantity: "1",
    },
    {
      level: 2,
      parent_code: "50250258",
      parent_description: "CONJUNTO TERMOSTATO",
      component_code: "10080626",
      description: "PROTETOR TERMICO",
      type: "MP",
      unit: "PC",
      quantity_per: "1000",
      accumulated_quantity: "1000",
    },
  ];

  it("expõe filtros com rótulos PT-BR das colunas da API", () => {
    const { fieldLabels } = buildFieldLabelsFromTableColumns(columns);
    const options = buildCategoryFilterOptions(
      rows,
      columns.map((column) => column.key),
      fieldLabels,
    );

    const labels = options.map((option) => option.label);

    expect(labels).toContain("Código pai");
    expect(labels).toContain("Descrição pai");
    expect(labels).toContain("Componente");
    expect(labels).not.toContain("Parent Code");
    expect(labels).not.toContain("Component Code");
  });
});
