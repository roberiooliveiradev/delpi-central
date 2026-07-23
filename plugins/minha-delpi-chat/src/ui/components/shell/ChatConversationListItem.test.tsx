import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const base = dirname(fileURLToPath(import.meta.url));

describe("ChatConversationListItem — botão direito", () => {
  it("expõe onContextMenu sem selecionar no direito; esquerdo usa onClick/nav", () => {
    const itemSrc = readFileSync(join(base, "ChatConversationListItem.tsx"), "utf8");
    const listSrc = readFileSync(join(base, "ChatSidebarSessionList.tsx"), "utf8");
    expect(itemSrc).toMatch(/onContextMenu\?:/);
    expect(itemSrc).toMatch(/só o clique esquerdo ativa a sessão/i);
    expect(itemSrc).toMatch(/onContextMenu=\{handleContextMenu\}/);
    expect(listSrc).toMatch(/onContextMenu=\{\(\) => setOpenMenuSessionId\(session\.id\)\}/);
  });
});
