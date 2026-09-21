import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(dir, "InteractionRoomsPage.tsx"), "utf8");

describe("InteractionRoomsPage", () => {
  it("usa a página canônica do kit e só entrega dados do processo", () => {
    expect(source).toMatch(/InteractionRoomPage/);
    expect(source).toMatch(/fillViewport/);
    expect(source).toMatch(/INTERACTION_ROOM_PAGE_LABELS_PT/);
    expect(source).toMatch(/Não lidas/);
    expect(source).toMatch(/Menções/);
    expect(source).toMatch(/Abrir processo/);
    expect(source).toMatch(/portalScopeClassName=\{TM_PORTAL_SCOPE\}/);
    expect(source).toMatch(/useDirectoryUserLabels/);
    expect(source).toMatch(/usePersonProfilePhotoUrls/);
    expect(source).toMatch(/onSaveEdit/);
    expect(source).toMatch(/onRemoveAttachment/);
    expect(source).toMatch(/resolveAttachmentImageSrc/);
    expect(source).toMatch(/onAttachmentImageClick/);
    expect(source).toMatch(/rewriteInlinePendingInMarkdown/);
    expect(source).toMatch(/onInlineImagesInserted/);
    expect(source).toMatch(/onLoadOlder/);
    expect(source).toMatch(/beforeId/);
    expect(source).toMatch(/onCreateTask/);
    expect(source).toMatch(/TaskEditorFrame/);
    expect(source).toMatch(/surface="bare"/);
    expect(source).toMatch(/HostContainedWideDialog/);
    expect(source).toMatch(/hideActions/);
    expect(source).toMatch(/source_interaction_message_id/);
    expect(source).toMatch(/useConfirm/);
    expect(source).not.toMatch(/window\.confirm/);
    expect(source).toMatch(/FilePreviewModal/);
    expect(source).toMatch(/findAttachment/);
    expect(source).not.toMatch(/<RoomConversationShell[\s/>]/);
    expect(source).not.toMatch(/<MentionComposer[\s/>]/);
    expect(source).not.toMatch(/<textarea\b/);
    expect(source).not.toMatch(/\bMurais\b/);
    expect(source).not.toMatch(/from ["']@delpi\/commercial/);
    expect(source).not.toMatch(/WebSocket|commercial\.interaction|commercial\.access/);
    expect(source).not.toMatch(/Renomear conversa|Excluir conversa/);
  });
});
