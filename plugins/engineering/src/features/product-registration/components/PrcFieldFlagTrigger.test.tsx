import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import {
  findOpenFieldFlag,
  findOpenSupplierFlag,
} from "./PrcFieldFlagTrigger";

const here = dirname(fileURLToPath(import.meta.url));

describe("PrcFieldFlagTrigger — D16-REF-02", () => {
  it("módulo não importa mais Plus (apenas Flag)", () => {
    const src = readFileSync(join(here, "PrcFieldFlagTrigger.tsx"), "utf8");
    expect(src).toMatch(/import\s*\{\s*Flag\s*\}\s*from\s*"lucide-react"/);
    expect(src).not.toMatch(/import\s*\{[^}]*\bPlus\b/);
    expect(src).not.toMatch(/<\s*Plus\b/);
    expect(src).toMatch(/Flag size=\{14\}/);
  });

  it("CSS do acionador sem OPEN é azul (--add)", () => {
    const css = readFileSync(join(here, "../prc.css"), "utf8");
    expect(css).toMatch(
      /\.engineering-prc__field-flag--add\s*\{[^}]*#2563eb/s,
    );
    expect(css).toMatch(/D16-REF-02/);
  });

  it("findOpenFieldFlag distingue OPEN de RESOLVED", () => {
    const flags = [
      {
        id: "1",
        requestId: "r",
        title: "a",
        description: "d",
        status: "RESOLVED" as const,
        subject: "FIELD" as const,
        targetPath: "description",
        version: 1,
        createdAt: "",
        createdBy: { subject: "u" },
        updatedAt: "",
        updatedBy: {},
      },
      {
        id: "2",
        requestId: "r",
        title: "b",
        description: "d",
        status: "OPEN" as const,
        subject: "FIELD" as const,
        targetPath: "description",
        version: 1,
        createdAt: "",
        createdBy: { subject: "u" },
        updatedAt: "",
        updatedBy: {},
      },
    ];
    expect(findOpenFieldFlag(flags, "description")?.id).toBe("2");
    expect(findOpenFieldFlag(flags, "group")).toBeUndefined();
  });

  it("findOpenSupplierFlag filtra por atributo SA5", () => {
    const flags = [
      {
        id: "3",
        requestId: "r",
        title: "pn",
        description: "d",
        status: "OPEN" as const,
        subject: "SUPPLIER_LINK" as const,
        targetAttribute: "partNumber" as const,
        supplierKey: { supplierCode: "000001", store: "01" },
        version: 1,
        createdAt: "",
        createdBy: { subject: "u" },
        updatedAt: "",
        updatedBy: {},
      },
    ];
    expect(
      findOpenSupplierFlag(flags, "000001", "01", "partNumber")?.id,
    ).toBe("3");
    expect(
      findOpenSupplierFlag(flags, "000001", "01", "catalogNumber"),
    ).toBeUndefined();
  });
});
