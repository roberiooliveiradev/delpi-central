import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("coedição na top bar", () => {
  it("aviso Também editando fica no head-trail do chrome, não solto na página", () => {
    const chrome = readFileSync(join(here, "DeckEditorChrome.tsx"), "utf8");
    const page = readFileSync(join(here, "../pages/PlaylistEditorPage.tsx"), "utf8");
    expect(chrome).toMatch(/td-deck-chrome__head-trail/);
    expect(chrome).toMatch(/editingPresence/);
    expect(chrome).toMatch(/td-editor-presence/);
    expect(page).toMatch(/editingPresence:/);
    expect(page).not.toMatch(/className="td-editor-presence"/);
  });
});
