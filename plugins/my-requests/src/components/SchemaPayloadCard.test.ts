import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  hasDedicatedPayloadPanel,
  schemaPayloadFields,
} from "../domain/schemaPayload";
import type { RequestTypeSummary } from "../types/requests";

const GENERAL_REQUEST_TYPE: RequestTypeSummary = {
  id: "type-1",
  code: "raw-material-creation",
  name: "Criação de Matéria-prima",
  active: true,
  presentation_mode: "schema_driven",
  branch_scope: "optional",
  permission_prefix: "my-requests.raw-material-creation",
  form_schema: {
    type: "object",
    required: ["title", "description"],
    properties: {
      title: { type: "string", minLength: 3, title: "Título" },
      description: { type: "string", minLength: 10, title: "Descrição" },
    },
    additionalProperties: false,
  },
  ui_schema: {
    title: { hint: "Resumo curto do que você precisa." },
    description: { widget: "textarea" },
  },
};

describe("schemaPayloadFields", () => {
  it("renderiza título e descrição do payload com os labels do schema", () => {
    const fields = schemaPayloadFields(GENERAL_REQUEST_TYPE, {
      title: "Revisar procedimento",
      description: "Detalhar o passo a passo.",
    });
    expect(fields.map((f) => f.label)).toEqual(["Título", "Descrição"]);
    expect(fields.map((f) => f.value)).toEqual([
      "Revisar procedimento",
      "Detalhar o passo a passo.",
    ]);
    expect(fields[1].hint).toBeUndefined();
    expect(fields[0].hint).toBe("Resumo curto do que você precisa.");
  });

  it("ignora campos não escalares e preenche ausentes com fallback", () => {
    const fields = schemaPayloadFields(GENERAL_REQUEST_TYPE, {
      title: { nested: true },
      description: "  ",
    });
    expect(fields).toEqual([
      { name: "description", label: "Descrição", hint: undefined, value: "—" },
    ]);
  });

  it("retorna vazio para tipos com painel dedicado ou modo especializado", () => {
    expect(hasDedicatedPayloadPanel("process-issue")).toBe(true);
    expect(hasDedicatedPayloadPanel("general-request")).toBe(true);
    expect(hasDedicatedPayloadPanel("raw-material-creation")).toBe(false);
    expect(
      schemaPayloadFields(
        { ...GENERAL_REQUEST_TYPE, code: "process-issue" },
        { title: "x", description: "y" },
      ),
    ).toEqual([]);
    expect(
      schemaPayloadFields(
        { ...GENERAL_REQUEST_TYPE, presentation_mode: "specialized" },
        { title: "x", description: "y" },
      ),
    ).toEqual([]);
  });

  it("retorna vazio sem schema, tipo ou payload", () => {
    expect(schemaPayloadFields(null, { title: "x" })).toEqual([]);
    expect(
      schemaPayloadFields({ ...GENERAL_REQUEST_TYPE, form_schema: {} }, { title: "x" }),
    ).toEqual([]);
    expect(schemaPayloadFields(GENERAL_REQUEST_TYPE, null)).toEqual([]);
  });
});

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function read(rel: string): string {
  return readFileSync(join(root, rel), "utf8");
}

describe("SchemaPayloadCard structural", () => {
  it("usa o mapeador canônico de schema — não reimplementa form_schema", () => {
    const card = read("components/SchemaPayloadCard.tsx");
    expect(card).toContain("schemaPayloadFields");
    expect(card).toContain("DetailFields");
    expect(card).toContain("Dados do formulário");
    const domain = read("domain/schemaPayload.ts");
    expect(domain).toContain("mapFormSchemaToFields");
  });

  it("detalhe busca o tipo e monta o card após os painéis dedicados", () => {
    const src = read("pages/RequestDetailPage.tsx");
    expect(src).toContain("getRequestType");
    expect(src).toContain("SchemaPayloadCard");
    const idxPanel = src.indexOf('request.type_code === "process-issue"');
    const idxCard = src.indexOf("<SchemaPayloadCard");
    const idxAttach = src.indexOf("<AttachmentsPanel");
    expect(idxPanel).toBeGreaterThan(-1);
    expect(idxCard).toBeGreaterThan(idxPanel);
    expect(idxAttach).toBeGreaterThan(idxCard);
  });
});
