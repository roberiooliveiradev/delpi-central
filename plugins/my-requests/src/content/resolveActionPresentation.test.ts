import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { resolveActionPresentation } from "./resolveActionPresentation";

describe("resolveActionPresentation", () => {
  it("centraliza label, variant, ícone e help sem inventar workflow", () => {
    const start = resolveActionPresentation("start");
    expect(start.label).toBe("Iniciar atendimento");
    expect(start.variant).toBe("primary");
    expect(start.Icon.displayName || start.Icon.name).toBeTruthy();
    expect(start.help.length).toBeGreaterThan(10);

    const cancel = resolveActionPresentation("cancel");
    expect(cancel.variant).toBe("ghost");
    expect(cancel.label).toBe("Cancelar solicitação");

    const edit = resolveActionPresentation("edit");
    expect(edit.label).toBe("Corrigir dados");
  });
});

describe("ActionBar structural", () => {
  it("usa HintAction, ícones e allowed_actions render-only", () => {
    const root = join(dirname(fileURLToPath(import.meta.url)), "..");
    const bar = readFileSync(join(root, "components/ActionBar.tsx"), "utf8");
    expect(bar).toMatch(/HintAction/);
    expect(bar).toMatch(/resolveActionPresentation/);
    expect(bar).toMatch(/filterDetailBarActions/);
    expect(bar).toMatch(/<Icon/);
    expect(bar).not.toMatch(/allowed_actions\s*=/);
  });
});
