import { cleanup, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it } from "vitest";

import { RoomSidePanel, roomSidePanelBemClasses } from "./RoomSidePanel";

const classNames = roomSidePanelBemClasses("test");
const stylesDir = join(dirname(fileURLToPath(import.meta.url)), "../../styles");

afterEach(() => {
  cleanup();
});

describe("RoomSidePanel", () => {
  it("mantém aside colapsado quando fechado (transição suave)", () => {
    const { container } = render(
      <RoomSidePanel classNames={classNames} title="Neste chat" open={false}>
        <p>Sobre</p>
      </RoomSidePanel>,
    );
    const aside = container.querySelector("aside");
    expect(aside?.className).toMatch(/delpi-ui-room-side-panel--collapsed/);
    expect(aside?.getAttribute("aria-hidden")).toBe("true");
    expect(screen.queryByText("Neste chat")).toBeNull();
  });

  it("mostra título e filhos sem botão fechar", () => {
    render(
      <RoomSidePanel classNames={classNames} title="Neste chat" open>
        <p>Participantes</p>
      </RoomSidePanel>,
    );
    const aside = screen.getByRole("complementary", { name: "Neste chat" });
    expect(aside.className).toMatch(/test-room-side-panel/);
    expect(aside.className).toMatch(/delpi-ui-room-side-panel/);
    expect(screen.getByRole("heading", { name: "Neste chat" })).toBeTruthy();
    expect(screen.getByText("Participantes")).toBeTruthy();
    expect(screen.queryByRole("button")).toBeNull();
  });
});

describe("room-side-panel.css", () => {
  it("é coluna de surface sem overlay nem divisor no título", () => {
    const css = readFileSync(join(stylesDir, "room-side-panel.css"), "utf8");
    expect(css).not.toMatch(/position:\s*fixed/);
    expect(css).not.toMatch(/inset:\s*0/);
    expect(css).toMatch(/flex:\s*0 0 min\(20rem, 36%\)/);
    expect(css).toMatch(/--collapsed/);
    expect(css).toMatch(/prefers-reduced-motion/);
    expect(css).toMatch(/\.delpi-ui-room-side-panel__title \{[\s\S]*?border:\s*none;/);
  });
});
