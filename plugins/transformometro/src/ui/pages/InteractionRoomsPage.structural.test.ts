import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(dir, "InteractionRoomsPage.tsx"), "utf8");

describe("InteractionRoomsPage", () => {
  it("usa o chrome compartilhado em texto puro, sem domínio comercial", () => {
    expect(source).toMatch(/RoomInboxList/);
    expect(source).toMatch(/RoomHeader/);
    expect(source).toMatch(/RoomConversationChatColumn/);
    expect(source).toMatch(/MessageThread/);
    expect(source).toMatch(/renderBody/);
    expect(source).toMatch(/LoadingActivityCard/);
    expect(source).toMatch(/Nenhuma interação ainda/);
    expect(source).toMatch(/Abra um processo para iniciar uma interação/);
    expect(source).not.toMatch(/MentionComposer/);
    expect(source).not.toMatch(/RoomConversationShell/);
    expect(source).not.toMatch(/dangerouslySetInnerHTML/);
    expect(source).not.toMatch(/from ["']@delpi\/commercial/);
    expect(source).not.toMatch(/WebSocket|commercial\.interaction|commercial\.access/);
  });
});
