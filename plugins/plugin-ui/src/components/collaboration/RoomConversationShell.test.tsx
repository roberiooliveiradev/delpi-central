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

  it("ChatColumn coloca o dock dentro do stage (composer no rodapé)", () => {
    const source = readFileSync(join(dir, "RoomConversationShell.tsx"), "utf8");
    const start = source.indexOf("export function RoomConversationChatColumn");
    const end = source.indexOf(
      "export type RoomConversationShellProps",
      start,
    );
    const column = source.slice(start, end > start ? end : undefined);
    expect(column).toMatch(/className=\{classNames\.stage\}/);
    expect(column).toMatch(/className=\{classNames\.dock\}/);
    expect(column).not.toMatch(/<>/);
    expect(column.indexOf("classNames.dock")).toBeGreaterThan(
      column.indexOf("classNames.msgs"),
    );
  });

  it("CSS canônico cobre thread e painel embutido", () => {
    const css = readFileSync(
      join(stylesDir, "room-conversation-shell.css"),
      "utf8",
    );
    expect(css).toMatch(/\.delpi-ui-room-thread \{/);
    expect(css).toMatch(/\.delpi-ui-room-thread__stage \{/);
    expect(css).toMatch(
      /\.delpi-ui-room-thread__stage \{[\s\S]*?grid-template-rows:\s*minmax\(0,\s*1fr\)\s+auto;/,
    );
    expect(css).toMatch(
      /\.delpi-ui-room-thread__main > \[class\*="-view-transition"\] > \[role="tabpanel"\]/,
    );
    expect(css).toMatch(/\.delpi-ui-room-thread__msgs \{[\s\S]*?overflow-y:\s*auto;/);
    expect(css).toMatch(/\.delpi-ui-room-thread__dock \{/);
    expect(css).toMatch(
      /\.delpi-ui-room-thread__dock \{[\s\S]*?background:\s*transparent;/,
    );
    expect(css).toMatch(/\.delpi-ui-room-panel \{/);
    expect(css).toMatch(
      /\.delpi-ui-room-thread__msgs > \.delpi-ui-soft-empty/,
    );
  });
});
