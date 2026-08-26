import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("InteractionRoomsInboxPage", () => {
  it("compõe RoomInboxList do kit sem bubble/textarea local", () => {
    const source = readFileSync(join(dir, "InteractionRoomsInboxPage.tsx"), "utf8");
    expect(source).toMatch(/CommercialRoomInboxList/);
    expect(source).toMatch(/CommercialRoomInboxPanel/);
    expect(source).toMatch(/CommercialCatalogSearchBar/);
    expect(source).toMatch(/CommercialScopeChipBar/);
    expect(source).not.toMatch(/CommercialUnderlineNav/);
    expect(source).toMatch(/listInteractionRooms/);
    expect(source).toMatch(/useInteractionInboxSync/);
    expect(source).toMatch(/CommercialSectionCard/);
    expect(source).not.toMatch(/CommercialPageHero/);
    expect(source).not.toMatch(/CommercialPagePath/);
    expect(source).toMatch(/cm-room-inbox-search/);
    expect(source).toMatch(/cm-room-inbox-pane__toolbar/);
    expect(source).toMatch(/cm-room-inbox-pane__filters/);
    expect(source).toMatch(/reloadLabel/);
    expect(readFileSync(join(dir, "../../content/interactionRoomsContent.ts"), "utf8")).toMatch(
      /reloadLabel:\s*"Tentar de novo"/,
    );
    expect(source).not.toMatch(/deleteInteractionRoom/);
    expect(source).not.toMatch(/actions=\{/);
    expect(source).not.toMatch(/Trash2/);
    expect(source).toMatch(/CustomerAvatar/);
    expect(source).toMatch(/selectedRoomId/);
    expect(source).toMatch(/inboxCustomerAvatarName/);
    expect(source).toMatch(/customer_name/);
    expect(source).not.toMatch(/name=\{dto\.title\}/);
    expect(source).toMatch(/accountLinkTitle/);
    expect(source).toMatch(/buildCustomerDetailHref/);
    expect(source).toMatch(/stopPropagation/);
    expect(source).toMatch(/markdownToPlainPreview/);
    expect(source).toMatch(/last_message_preview/);
    expect(source).toMatch(/CommercialLoadingCard/);
    expect(source).toMatch(/CommercialEmptyGuidance/);
    expect(source).toMatch(/inboxFilterEmptyWallTitle/);
    expect(source).toMatch(/unreadBadgeLabel/);
    expect(source).toMatch(/unread_count|unreadCount/);
    expect(source).toMatch(/inboxEmptyCopy/);
    expect(source).toMatch(/resolveInboxLoadingState/);
    expect(source).toMatch(/inboxRefreshingLabel/);
    expect(source).toMatch(/CommercialViewTransition/);
    expect(source).toMatch(/transitionKey=\{\`\$\{filter\}:\$\{query\.trim\(\)\}\`\}/);
  });
});
