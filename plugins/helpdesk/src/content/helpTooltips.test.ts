import { describe, expect, it } from "vitest";

import { helpTooltips } from "./helpTooltips";

const SECTION_MAX = 160;
const FIELD_MAX = 120;

function collectStrings(value: unknown, path = ""): Array<{ path: string; text: string }> {
  if (typeof value === "string") return [{ path: path || "root", text: value }];
  if (value && typeof value === "object") {
    return Object.entries(value as Record<string, unknown>).flatMap(([key, child]) =>
      collectStrings(child, path ? `${path}.${key}` : key),
    );
  }
  return [];
}

describe("helpTooltips budget", () => {
  const entries = collectStrings(helpTooltips);

  it("seções principais cabem em uma frase curta", () => {
    for (const key of ["list", "link", "create", "detail"] as const) {
      expect(helpTooltips[key].length, key).toBeLessThanOrEqual(SECTION_MAX);
    }
  });

  it("nenhum tooltip passa do teto de campo", () => {
    const oversized = entries.filter((entry) => entry.text.length > FIELD_MAX);
    expect(oversized).toEqual([]);
  });

  it("cobre anexar/colar/arrastar na abertura e na resposta", () => {
    expect(helpTooltips.createUi.attach).toMatch(/anex|arrastar/i);
    expect(helpTooltips.createUi.description).toMatch(/cole|clipe|anex|arrastar|@|mencion/i);
    expect(helpTooltips.detailUi.attach).toMatch(/anex|arrastar/i);
    expect(helpTooltips.detailUi.reply).toMatch(/cole|clipe|anex|arrastar|@|mencion/i);
    expect(helpTooltips.detailUi.attachments).toMatch(/arquivo/i);
  });

  it("cobre atribuição de técnico na abertura e no detalhe", () => {
    expect(helpTooltips.createUi.assignee).toMatch(/Minha DELPI|e-mail|email/i);
    expect(helpTooltips.detailUi.assignee).toMatch(/Minha DELPI|e-mail|email|atribu/i);
    expect(helpTooltips.detailUi.assigneeAction).toMatch(/atribui/i);
  });

  it("cobre ciclo H10 aceitar/recusar/satisfação", () => {
    expect(helpTooltips.detailUi.acceptSolution).toMatch(/aceit|fecha/i);
    expect(helpTooltips.detailUi.rejectSolution).toMatch(/recus|reabre/i);
    expect(helpTooltips.detailUi.submitSatisfaction).toMatch(/nota|1 a 5|avalia/i);
  });

  it("cobre aprovação TicketValidation", () => {
    expect(helpTooltips.detailUi.acceptValidation).toMatch(/aceit|aprova/i);
    expect(helpTooltips.detailUi.rejectValidation).toMatch(/recus|aprova/i);
    expect(helpTooltips.detailUi.observersRead).toMatch(/somente leitura|observ/i);
    expect(helpTooltips.detailUi.slaLevelName).toMatch(/nível|prazo/i);
    expect(helpTooltips.detailUi.slaLevelName).not.toMatch(/deadline|HLAPI|DTO/i);
    expect(helpTooltips.detailUi.approvalsSurface).toMatch(/aprova/i);
  });

  it("cobre ações operacionais do workspace (solução/tarefa/aprovação)", () => {
    expect(helpTooltips.detailUi.actionMenu).toMatch(/solução|tarefa|aprova/i);
    expect(helpTooltips.detailUi.createSolution).toMatch(/solução/i);
    expect(helpTooltips.detailUi.createTask).toMatch(/tarefa/i);
    expect(helpTooltips.detailUi.requestApproval).toMatch(/aprova/i);
    expect(helpTooltips.detailUi.requestApproval).toMatch(/grupo|usuário/i);
    expect(helpTooltips.detailUi.attachFile).toMatch(/arquivo/i);
  });

  it("centraliza helps dos action cards em actionFields", () => {
    const fields = helpTooltips.detailUi.actionFields;
    expect(fields.reply.model).toMatch(/modelo/i);
    expect(fields.reply.source).toMatch(/origem/i);
    expect(fields.solution.type).toMatch(/classifica/i);
    expect(fields.task.duration).toMatch(/minutos/i);
    expect(fields.task.assignee).toMatch(/técnico/i);
    expect(fields.attachment.title).toMatch(/arquivo/i);
    expect(fields.approval.approverType).toMatch(/usuário|grupo/i);
  });

  it("não reintroduz o bloco filters órfão da FiltersRow antiga", () => {
    expect(helpTooltips).not.toHaveProperty("filters");
  });
});
