import { cleanup, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it, vi } from "vitest";

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

  it("renderiza slot nav após avatares e antes de actions", () => {
    const { container } = render(
      <RoomHeader
        classNames={classNames}
        title="Pedido 1"
        participantsAriaLabel="Members"
        participants={[{ id: "1", name: "Ana Silva" }]}
        nav={<nav aria-label="Vista">Chat</nav>}
        actions={<button type="button">Search</button>}
      />,
    );
    const people = container.querySelector(".delpi-ui-room-header__people");
    expect(people).toBeTruthy();
    const nav = people?.querySelector(".delpi-ui-room-header__nav");
    const actions = people?.querySelector(".delpi-ui-room-header__actions");
    expect(screen.getByRole("navigation", { name: "Vista" })).toBeTruthy();
    expect(nav).toBeTruthy();
    expect(actions).toBeTruthy();
    const children = [...(people?.children ?? [])];
    expect(children.indexOf(nav as Element)).toBeGreaterThan(
      children.findIndex((el) => el.getAttribute("aria-label") === "Members"),
    );
    expect(children.indexOf(nav as Element)).toBeLessThan(
      children.indexOf(actions as Element),
    );
  });

  it("título clicável abre entidade via onTitleClick", () => {
    const onTitleClick = vi.fn();
    render(
      <RoomHeader
        classNames={classNames}
        title="Pedido 002573"
        onTitleClick={onTitleClick}
        titleActionLabel="Abrir pedido"
      />,
    );
    const button = screen.getByRole("button", { name: "Abrir pedido" });
    expect(button.textContent).toBe("Pedido 002573");
    button.click();
    expect(onTitleClick).toHaveBeenCalledTimes(1);
  });

  it("header CSS fica em uma linha com ellipsis no título", () => {
    const css = readFileSync(join(stylesDir, "room-header.css"), "utf8");
    const root = css.match(/\.delpi-ui-room-header \{[^}]+\}/)?.[0] ?? "";
    const title = css.match(/\.delpi-ui-room-header__title \{[^}]+\}/)?.[0] ?? "";
    expect(root).toMatch(/flex-wrap:\s*nowrap;/);
    expect(root).toMatch(/align-items:\s*center;/);
    expect(title).toMatch(/text-overflow:\s*ellipsis;/);
    expect(css).toMatch(/\.delpi-ui-room-header__chip \{/);
    expect(css).toMatch(/\.delpi-ui-room-header__nav \{/);
    expect(css).toMatch(/\.delpi-ui-room-header__title-button \{/);
    expect(css).toMatch(
      /\.delpi-ui-room-header__people \[aria-pressed="true"\]/,
    );
    expect(css).toMatch(/--delpi-ui-room-header-control-gap/);
    expect(css).toMatch(
      /\.delpi-ui-room-header__people > \.delpi-ui-room-header__nav/,
    );
    expect(css).toMatch(/display:\s*contents/);
  });
});
