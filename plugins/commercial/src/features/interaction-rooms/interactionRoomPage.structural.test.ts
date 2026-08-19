import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("InteractionRoomPage", () => {
  it("compõe RoomHeader + MessageThread + composer com anexos", () => {
    const source = readFileSync(join(dir, "InteractionRoomPage.tsx"), "utf8");
    expect(source).toMatch(/CommercialRoomHeader/);
    expect(source).toMatch(/interactionRoomAuthorAvatarFields/);
    expect(source).toMatch(/interactionRoomParticipantAvatar/);
    expect(source).toMatch(/CommercialMessageThread/);
    expect(source).toMatch(/resolveActions/);
    expect(source).toMatch(/CommercialMessageThread/);
    expect(source).not.toMatch(/cm-message-thread__actions/);
    expect(source).toMatch(/createTaskFromInteractionMessage/);
    expect(source).toMatch(/InteractionRoomMessageComposer/);
    expect(source).toMatch(/useDirectoryUserLabels/);
    expect(source).toMatch(/nameFor/);
    expect(source).toMatch(/usePortfolioScope/);
    expect(source).toMatch(/mine:/);
    expect(source).toMatch(/CommercialConversationFileDropLayer/);
    expect(source).toMatch(/CommercialRoomContextPanel/);
    expect(source).toMatch(/CommercialRoomSidePanel/);
    expect(source).not.toMatch(/CommercialSectionCard/);
    expect(source).toMatch(/embedded/);
    expect(source).toMatch(/flush/);
    expect(source).not.toMatch(/CommercialHostDrawer/);
    expect(source).not.toMatch(/portalTarget/);
    expect(source).toMatch(/cm-room-thread__stage/);
    expect(source).toMatch(/CommercialAlertQueue/);
    expect(source).toMatch(/cm-room-alert-host/);
    expect(source).toMatch(/onRoomTitle/);
    expect(source).toMatch(/contextToggle/);
    expect(source).not.toMatch(/CommercialStateBanner/);
    expect(source).not.toMatch(/CommercialStatusBadge/);
    expect(source).not.toMatch(/aria-hidden \/>\s*\{content\.contextToggle\}/);
    expect(source).toMatch(/scrollThreadMessageIntoView/);
    expect(source).toMatch(/shouldStickThreadToBottom/);
    expect(source).toMatch(/useInteractionRoomSync/);
    expect(source).toMatch(/applyInteractionRoomRealtime/);
    expect(source).not.toMatch(/cm-message-bubble/);
    expect(source).not.toMatch(/<textarea/);
  });
});
