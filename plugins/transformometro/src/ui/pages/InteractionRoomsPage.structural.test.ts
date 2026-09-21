import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(dir, "InteractionRoomsPage.tsx"), "utf8");

describe("InteractionRoomsPage", () => {
  it("usa a página canônica do kit e só entrega dados do processo", () => {
    expect(source).toMatch(/InteractionRoomPage/);
    expect(source).toMatch(/INTERACTION_ROOM_PAGE_LABELS_PT/);
    expect(source).toMatch(/Não lidas/);
    expect(source).toMatch(/Menções/);
    expect(source).toMatch(/Abrir processo/);
    expect(source).toMatch(/portalScopeClassName=\{TM_PORTAL_SCOPE\}/);
    expect(source).toMatch(/useDirectoryUserLabels/);
    expect(source).toMatch(/onSaveEdit/);
    expect(source).toMatch(/FilePreviewModal/);
    expect(source).not.toMatch(/<RoomConversationShell[\s/>]/);
    expect(source).not.toMatch(/<MentionComposer[\s/>]/);
    expect(source).not.toMatch(/<textarea\b/);
    expect(source).not.toMatch(/\bMurais\b/);
    expect(source).not.toMatch(/from ["']@delpi\/commercial/);
    expect(source).not.toMatch(/WebSocket|commercial\.interaction|commercial\.access/);
    expect(source).not.toMatch(/Renomear conversa|Excluir conversa/);
  });
});
