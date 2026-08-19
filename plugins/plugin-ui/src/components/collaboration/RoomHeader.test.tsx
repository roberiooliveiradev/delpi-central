import { cleanup, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it } from "vitest";

import { RoomHeader, roomHeaderBemClasses } from "./RoomHeader";

const classNames = roomHeaderBemClasses("test");
const stylesDir = join(dirname(fileURLToPath(import.meta.url)), "../../styles");

afterEach(() => {
  cleanup();
});

describe("RoomHeader", () => {
  it("renders title, chips slot and participants", () => {
    render(
      <RoomHeader
        classNames={classNames}
        title="Pedido 102942"
        subtitle="Entity room"
        chips={<span>SC</span>}
        participantsAriaLabel="Members"
        participants={[
          { id: "1", name: "Ana Silva" },
          { id: "2", name: "Bruno Costa" },
        ]}
        actions={<button type="button">Invite</button>}
      />,
    );
    expect(screen.getByRole("heading", { name: "Pedido 102942" })).toBeTruthy();
    expect(screen.getByText("SC")).toBeTruthy();
    expect(screen.getByLabelText("Members")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Invite" })).toBeTruthy();
  });

  it("header CSS fica em uma linha com ellipsis no título", () => {
    const css = readFileSync(join(stylesDir, "room-header.css"), "utf8");
    const root = css.match(/\.delpi-ui-room-header \{[^}]+\}/)?.[0] ?? "";
    const title = css.match(/\.delpi-ui-room-header__title \{[^}]+\}/)?.[0] ?? "";
    expect(root).toMatch(/flex-wrap:\s*nowrap;/);
    expect(root).toMatch(/align-items:\s*center;/);
    expect(title).toMatch(/text-overflow:\s*ellipsis;/);
  });
});
