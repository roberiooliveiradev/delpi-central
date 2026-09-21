import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("CommercialInteractionRoomHost", () => {
  it("usa kit InteractionRoomPage layout=thread com slots de domínio", () => {
    const source = readFileSync(
      join(dir, "CommercialInteractionRoomHost.tsx"),
      "utf8",
    );
    expect(source).toMatch(/from "@delpi\/plugin-ui\/index"/);
    expect(source).toMatch(
      /InteractionRoomPage as KitInteractionRoomPage/,
    );
    expect(source).toMatch(/layout="thread"/);
    expect(source).toMatch(/cm-interaction-room-host/);
    expect(source).toMatch(/prefix="cm"/);
    expect(source).toMatch(/portalScopeClassName=\{CM_PORTAL_SCOPE\}/);
    expect(source).toMatch(/resolveExtraActions/);
    expect(source).toMatch(/buildCreateTaskMessageAction/);
    expect(source).toMatch(/renderComposer/);
    expect(source).toMatch(/InteractionRoomMessageComposer/);
    expect(source).toMatch(/resolveActionExtras/);
    expect(source).toMatch(/InteractionRoomMessageReactionQuickBar/);
    expect(source).toMatch(/InteractionRoomMessageReactions/);
    expect(source).toMatch(/InteractionRoomMessageAttachments/);
    expect(source).toMatch(/InteractionRoomMentionUnfurls/);
    expect(source).toMatch(/belowBody/);
    expect(source).toMatch(/pinned:/);
    expect(source).toMatch(/listRoomSharedItems/);
    expect(source).toMatch(/sharedItems=/);
    expect(source).toMatch(/headerMenu/);
    expect(source).toMatch(/InteractionRoomMoreMenu/);
    expect(source).toMatch(/useInteractionRoomSync/);
    expect(source).toMatch(/applyInteractionRoomRealtime/);
    expect(source).toMatch(/createTaskFromInteractionMessage/);
    expect(source).toMatch(/TaskAttachmentPreviewModal/);
    expect(source).toMatch(/inboxHref/);
    expect(source).toMatch(/onRoomTitle/);
    expect(source).toMatch(/inboxQuery=""/);
    expect(source).toMatch(/chips=\{\[\]\}/);
    expect(source).toMatch(/rooms=\{\[\]\}/);
    expect(source).not.toMatch(/onToggleReaction/);
    expect(source).not.toMatch(/CommercialRoomConversationShell/);
    expect(source).not.toMatch(/CommercialRoomConversationChatColumn/);
    expect(source).not.toMatch(/CommercialMessageThread/);
    expect(source).not.toMatch(/CommercialRoomHeader/);
    expect(source).not.toMatch(/CommercialRoomSidePanel/);
    expect(source).not.toMatch(/CommercialRoomMessageFindPanel/);
    expect(source).not.toMatch(/CommercialRoomContextPanel/);
    expect(source).not.toMatch(/sidePanelMode/);
    expect(source).not.toMatch(/setRoomView/);
    expect(source).not.toMatch(/shouldStickThreadToBottom/);
    expect(source).not.toMatch(/\bmsgsRef\b/);
    expect(source).not.toMatch(/InteractionRoomSharedView/);
    expect(source).toMatch(/mode=\{editingMessageId \? "edit" : "compose"\}/);
    expect(source).not.toMatch(/editingId=\{editingMessageId\}/);
    expect(source).not.toMatch(/renderEditSlot=/);
    expect(source).toMatch(/InteractionRoomRenameDialog/);
    expect(source).toMatch(/renameInteractionRoom/);
    expect(source).toMatch(/deleteInteractionRoom/);
    expect(source).toMatch(/canManagePortfolios/);
    expect(source).toMatch(/useCommercialConfirm/);
    expect(source).toMatch(/room\.deleted/);
    expect(source).toMatch(/room\.updated/);
    expect(source).toMatch(/room\.attachment/);
    expect(source).not.toMatch(/window\.confirm/);
    expect(source).not.toMatch(/<textarea/);
  });

  it("reexporta InteractionRoomPage do host", () => {
    const barrel = readFileSync(join(dir, "InteractionRoomPage.tsx"), "utf8");
    expect(barrel).toMatch(/CommercialInteractionRoomHost/);
    expect(barrel).toMatch(/InteractionRoomPage/);
    expect(barrel).toMatch(/from "\.\/CommercialInteractionRoomHost"/);
  });
});
