import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(dir, "InteractionRoomsPage.tsx"), "utf8");

describe("InteractionRoomsPage", () => {
  it("usa o mesmo canvas de conversas do kit, sem domínio comercial", () => {
    expect(source).toMatch(/Conversas/);
    expect(source).toMatch(/Buscar por título da sala/);
    expect(source).toMatch(/CatalogSearchBar/);
    expect(source).toMatch(/ScopeChipBar/);
    expect(source).toMatch(/RoomInboxList/);
    expect(source).toMatch(/InitialsAvatar/);
    expect(source).toMatch(/ResizableColumns/);
    expect(source).toMatch(/MentionComposer/);
    expect(source).toMatch(/showAttach=\{false\}/);
    expect(source).toMatch(/MessageThread/);
    expect(source).toMatch(/Nenhuma mensagem ainda/);
    expect(source).not.toMatch(/Não lidas|Menções|Murais/);
    expect(source).not.toMatch(/from ["']@delpi\/commercial/);
    expect(source).not.toMatch(/WebSocket|commercial\.interaction|commercial\.access/);
    expect(source).not.toMatch(/RoomConversationShell/);
  });
});
