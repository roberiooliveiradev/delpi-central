import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));
const featuresRoot = join(dir, "..");

describe("InteractionRoomPanel", () => {
  it("compõe SectionCard colapsável + Shell e resolve lazy", () => {
    const source = readFileSync(join(dir, "InteractionRoomPanel.tsx"), "utf8");
    expect(source).toMatch(/CommercialSectionCard/);
    expect(source).toMatch(/collapsible:\s*true/);
    expect(source).toMatch(/defaultOpen:\s*true/);
    expect(source).toMatch(/CM_HELP\.interactionRooms\.panel/);
    expect(source).toMatch(/hint:\s*CM_HELP\.interactionRooms\.panel/);
    expect(source).toMatch(/InteractionRoomConversationShell/);
    expect(source).toMatch(/InteractionRoomConversationChatColumn/);
    expect(source).toMatch(/cm-room-panel/);
    expect(source).toMatch(/CommercialRoomHeader/);
    expect(source).toMatch(/interactionRoomAuthorAvatarFields/);
    expect(source).toMatch(/interactionRoomParticipantAvatar/);
    expect(source).toMatch(/CommercialMessageThread/);
    expect(source).toMatch(/resolveActions/);
    expect(source).toMatch(/resolveActionExtras/);
    expect(source).toMatch(/portalScopeClassName=\{CM_PORTAL_SCOPE\}/);
    expect(source).toMatch(/messageActionsToolbarAriaLabel/);
    expect(source).toMatch(/InteractionRoomMessageReactionQuickBar/);
    expect(source).toMatch(/createTaskFromInteractionMessage/);
    expect(source).toMatch(/InteractionRoomMessageComposer/);
    expect(source).toMatch(/nameFor/);
    expect(source).toMatch(/useUserProfilePhotoUrls/);
    expect(source).toMatch(/photoByUserId/);
    expect(source).toMatch(/usePortfolioScope/);
    expect(source).toMatch(/mine:/);
    expect(source).not.toMatch(/CommercialConversationFileDropLayer/);
    expect(source).toMatch(/resolveInteractionRoom/);
    expect(source).toMatch(/useInteractionRoomSync/);
    expect(source).toMatch(/applyInteractionRoomRealtime/);
    expect(source).toMatch(/CommercialHostDrawer/);
    expect(source).toMatch(/INTERACTION_ROOM_NARROW_QUERY|max-width: 768px/);
    expect(source).toMatch(/mode=\{editingMessageId \? "edit" : "compose"\}/);
    expect(source).toMatch(/editBanner=\{editBanner\}/);
    expect(source).toMatch(/buildEditComposerBanner/);
    expect(source).not.toMatch(/editingId=\{editingMessageId\}/);
    expect(source).not.toMatch(/renderEditSlot=/);
    expect(source).not.toMatch(/disabled=\{Boolean\(editingMessageId\)\}/);
    expect(source).toMatch(/messageEditedAtTemplate/);
    expect(source).toMatch(/formatInteractionMessageCreatedAtLabel/);
    expect(source).toMatch(/onEditMessage:/);
    expect(source).toMatch(/onDeleteMessage:/);
    expect(source).toMatch(/useCommercialConfirm/);
    expect(source).toMatch(/deleteInteractionMessage/);
    expect(source).not.toMatch(/window\.confirm/);
    expect(source).toMatch(/onReplyMessage:/);
    expect(source).toMatch(/replyToMessageId=/);
    expect(source).toMatch(/InteractionRoomMessageReactions/);
    expect(source).toMatch(/InteractionRoomMessageAttachments/);
    expect(source).toMatch(/onMessageAttachmentsSettled/);
    expect(source).toMatch(/room\.attachment/);
    expect(source).not.toMatch(/<textarea/);
    expect(source).not.toMatch(/cm-message-bubble/);
  });

  it("está embutido nas quatro fichas (conta, pedido, OV, OP)", () => {
    const callSites = [
      join(featuresRoot, "customers/components/CustomerOverviewSection.tsx"),
      join(featuresRoot, "customers/pages/CustomerOrderDetailPage.tsx"),
      join(featuresRoot, "open-orders/OpenOrderLineDetailPage.tsx"),
      join(featuresRoot, "open-orders/OpenOrderOpDetailPage.tsx"),
    ];
    for (const path of callSites) {
      const source = readFileSync(path, "utf8");
      expect(source).toMatch(/InteractionRoomPanel/);
    }
  });
});
