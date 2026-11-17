/** MY-REQUESTS-JSON-PRESENTATION-CATALOG-TRANSITION-01 — regressão
 * estrutural: os cards de Nova solicitação NÃO podem voltar a renderizar
 * type.name/type.description direto como fonte primária; a copy vem do
 * catálogo JSON e a ordem visual vem de sortRequestTypesByPresentation. */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(resolve(dir, "NewRequestPage.tsx"), "utf-8");

describe("NewRequestPage — catálogo JSON de apresentação", () => {
  it("cards usam resolveRequestTypeCardCopy e ordem do JSON", () => {
    expect(src).toMatch(/resolveRequestTypeCardCopy/);
    expect(src).toMatch(/sortRequestTypesByPresentation/);
    expect(src).toMatch(/copy\.title/);
    expect(src).toMatch(/copy\.description/);
  });

  it("não volta a usar type.name como título do card", () => {
    expect(src).not.toMatch(/title=\{type\.name\}/);
    expect(src).not.toMatch(/aria-label=\{`Abrir \$\{type\.name\}`\}/);
  });

  it("mantém autoridade operacional: filtro por permissão e code real", () => {
    expect(src).toMatch(/canCreateRequestType/);
    expect(src).toMatch(/permission_prefix/);
    expect(src).toMatch(/type\.code/);
  });
});
