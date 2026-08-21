import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  createDashboardRoomConversationShell,
  roomConversationShellBemClasses,
} from "./RoomConversationShell";

const dir = dirname(fileURLToPath(import.meta.url));
const stylesDir = join(dir, "../../styles");

describe("RoomConversationShell", () => {
  it("emite dual-class room-thread e room-panel", () => {
    const cn = roomConversationShellBemClasses("cm");
    expect(cn.root).toMatch(/cm-room-thread/);
    expect(cn.root).toMatch(/delpi-ui-room-thread/);
    expect(cn.header).toMatch(/__header/);
    expect(cn.body).toMatch(/__body/);
    expect(cn.main).toMatch(/__main/);
    expect(cn.stage).toMatch(/__stage/);
    expect(cn.msgs).toMatch(/__msgs/);
    expect(cn.dock).toMatch(/__dock/);
    expect(cn.panel).toMatch(/cm-room-panel/);
    expect(cn.panel).toMatch(/delpi-ui-room-panel/);
  });

  it("factory expõe Shell, ChatColumn e Panel", () => {
    const { Shell, ChatColumn, Panel, classNames } =
      createDashboardRoomConversationShell("cm");
    expect(typeof Shell).toBe("function");
    expect(typeof ChatColumn).toBe("function");
    expect(typeof Panel).toBe("function");
    expect(classNames.root).toMatch(/delpi-ui-room-thread/);
  });

  it("CSS canônico cobre thread e painel embutido", () => {
    const css = readFileSync(
      join(stylesDir, "room-conversation-shell.css"),
      "utf8",
    );
    expect(css).toMatch(/\.delpi-ui-room-thread \{/);
    expect(css).toMatch(/\.delpi-ui-room-thread__stage \{/);
    expect(css).toMatch(/\.delpi-ui-room-thread__msgs \{[\s\S]*?overflow-y:\s*auto;/);
    expect(css).toMatch(/\.delpi-ui-room-thread__dock \{/);
    expect(css).toMatch(/\.delpi-ui-room-panel \{/);
  });
});
