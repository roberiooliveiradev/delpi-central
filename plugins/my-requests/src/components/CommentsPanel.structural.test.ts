import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { shouldStickThreadToBottom } from "../utils/threadStickToBottom";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function read(rel: string): string {
  return readFileSync(join(root, rel), "utf8");
}

describe("Request conversation structural", () => {
  it("usa MessageThread e MentionComposer do kit, sem commercial-api", () => {
    const panel = read("components/CommentsPanel.tsx");
    const mrUi = read("ui/mrUi.tsx");
    expect(panel).toMatch(/Conversa sobre a solicitação/);
    expect(panel).toMatch(/MyRequestsMessageThread/);
    expect(panel).toMatch(/MyRequestsMentionComposer/);
    expect(panel).toMatch(/MyRequestsRoomPanel/);
    expect(panel).toMatch(/is_mine/);
    expect(panel).toMatch(/authorSrc/);
    expect(panel).toMatch(/canComment/);
    expect(panel).toMatch(/formatToggleAriaLabel/);
    expect(panel).toMatch(/showAttach/);
    expect(panel).toMatch(/resolveAttachmentImageSrc/);
    expect(panel).not.toMatch(/showAttach=\{false\}/);
    expect(panel).not.toMatch(/my-requests-domain-list/);
    expect(panel).not.toMatch(/NativeTextAreaControl/);
    expect(panel).not.toMatch(/commercial-api/);
    expect(mrUi).toMatch(/createDashboardMessageThread/);
    expect(mrUi).toMatch(/createDashboardMentionComposer/);
    expect(mrUi).toMatch(/createDashboardRoomConversationShell/);
  });

  it("contem o RoomPanel no frame para não vazar sobre Artifacts", () => {
    const css = read("index.css");
    expect(css).toMatch(
      /\.my-requests-detail-conversation__frame\s*\{[^}]*overflow:\s*hidden/s,
    );
    expect(css).toMatch(/--delpi-ui-room-panel-height:\s*100%/);
    expect(css).toMatch(/--delpi-ui-room-panel-max-height:\s*100%/);
    expect(css).toMatch(/--delpi-ui-room-panel-min-height:\s*0/);
  });

  it("stick-to-bottom só perto do fundo", () => {
    expect(
      shouldStickThreadToBottom({
        scrollTop: 100,
        scrollHeight: 200,
        clientHeight: 100,
      }),
    ).toBe(true);
    expect(
      shouldStickThreadToBottom({
        scrollTop: 0,
        scrollHeight: 500,
        clientHeight: 100,
      }),
    ).toBe(false);
  });
});
