import { describe, expect, it } from "vitest";

import type { CommercialTaskDto } from "../../api/worklistApi";
import { commercialTaskMatchesQuery } from "./myDayTaskSearch";

const task = {
  id: "1",
  title: "Ligar para ACME",
  description: "Cliente pediu retorno da NF",
  task_type: "call",
  status: "open",
  priority: "normal",
  assignee_user_id: "u1",
  created_by_user_id: "u1",
  customer_name: "ACME Ltda",
  customer_code: "000123",
  assignee_groups: [{ id: "g1", name: "Vendas Sul" }],
} satisfies CommercialTaskDto;

describe("commercialTaskMatchesQuery", () => {
  it("consulta vazia mantém a tarefa do recorte", () => {
    expect(commercialTaskMatchesQuery(task, "   ", {})).toBe(true);
  });

  it("encontra título, observação, responsável, cliente e tipo sem diferenciar maiúsculas", () => {
    const extras = { assigneeLabels: ["Ana Souza"], typeLabel: "Ligação" };
    expect(commercialTaskMatchesQuery(task, "acme", extras)).toBe(true);
    expect(commercialTaskMatchesQuery(task, "retorno", extras)).toBe(true);
    expect(commercialTaskMatchesQuery(task, "ana", extras)).toBe(true);
    expect(commercialTaskMatchesQuery(task, "000123", extras)).toBe(true);
    expect(commercialTaskMatchesQuery(task, "ligação", extras)).toBe(true);
    expect(commercialTaskMatchesQuery(task, "inexistente", extras)).toBe(false);
  });
});
