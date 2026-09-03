import { describe, expect, it } from "vitest";

import { emptyValuesFromFields, mapFormSchemaToFields } from "./mapFormSchemaToFields";

const FORM = {
  type: "object",
  required: ["description", "unit"],
  properties: {
    description: { type: "string", minLength: 1, title: "Descrição" },
    unit: { type: "string", enum: ["UN", "KG", "M"], title: "Unidade" },
    notes: { type: "string", title: "Observações" },
  },
};

describe("mapFormSchemaToFields", () => {
  it("mapeia string/enum/textarea para kinds do kit", () => {
    const fields = mapFormSchemaToFields(FORM, { notes: { widget: "textarea" } });
    expect(fields.map((f) => f.name)).toEqual(["description", "unit", "notes"]);
    expect(fields[0]).toMatchObject({ kind: "text", required: true, label: "Descrição" });
    expect(fields[1]).toMatchObject({ kind: "select", required: true });
    expect(fields[1].options?.map((o) => o.value)).toEqual(["UN", "KG", "M"]);
    expect(fields[2]).toMatchObject({ kind: "textarea", required: false });
  });

  it("gera valores iniciais com default do enum", () => {
    const fields = mapFormSchemaToFields(FORM, { notes: { widget: "textarea" } });
    const values = emptyValuesFromFields(fields);
    expect(values.unit).toBe("UN");
    expect(values.description).toBe("");
  });
});
