import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  EXTERNAL_OPERATOR_ID_PREFIX,
  isExternalOperatorId,
} from "./externalIdentity";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function read(rel: string): string {
  return readFileSync(join(root, rel), "utf8");
}

describe("isExternalOperatorId", () => {
  it("reconhece IDs externos de operador", () => {
    expect(isExternalOperatorId("operator:02:001234")).toBe(true);
    expect(isExternalOperatorId("operator:01:9")).toBe(true);
    expect(isExternalOperatorId(" operator:02:1 ")).toBe(true);
  });

  it("não confunde usuários reais da Minha DELPI", () => {
    expect(isExternalOperatorId("user-123")).toBe(false);
    expect(isExternalOperatorId("joao.silva@delpi.com")).toBe(false);
    expect(isExternalOperatorId("OPERATOR:02:1")).toBe(false);
    expect(isExternalOperatorId(null)).toBe(false);
    expect(isExternalOperatorId(undefined)).toBe(false);
    expect(isExternalOperatorId("")).toBe(false);
  });

  it("expõe o prefixo canônico", () => {
    expect(EXTERNAL_OPERATOR_ID_PREFIX).toBe("operator:");
  });
});

describe("useParticipantAvatarUrls — externo", () => {
  it("não consulta avatar para IDs operator:*", () => {
    const hook = read("hooks/useParticipantAvatarUrls.ts");
    expect(hook).toContain("isExternalOperatorId");
    expect(hook).toMatch(/\.filter\(.*isExternalOperatorId/s);
  });
});

describe("consumidores usam o hook canônico", () => {
  it("detalhe, comentários e timeline compartilham o filtro", () => {
    for (const rel of [
      "pages/RequestDetailPage.tsx",
      "components/CommentsPanel.tsx",
      "components/TimelinePanel.tsx",
    ]) {
      expect(read(rel)).toContain("useParticipantAvatarUrls");
    }
  });
});
