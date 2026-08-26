import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RoomInboxList, RoomInboxPanel, roomInboxListBemClasses } from "./RoomInboxList";

const classNames = roomInboxListBemClasses("test");
const stylesDir = join(dirname(fileURLToPath(import.meta.url)), "../../styles");

afterEach(() => {
  cleanup();
});

describe("RoomInboxList", () => {
  it("renders empty state", () => {
    render(
      <RoomInboxList
        classNames={classNames}
        items={[]}
        listAriaLabel="Inbox"
        emptyLabel="No rooms"
      />,
    );
    expect(screen.getByRole("status").textContent).toBe("No rooms");
  });

  it("renders emptyContent slot when provided", () => {
    render(
      <RoomInboxList
        classNames={classNames}
        items={[]}
        listAriaLabel="Inbox"
        emptyLabel="No rooms"
        emptyContent={
          <div role="status">
            <h3>Custom empty</h3>
          </div>
        }
      />,
    );
    expect(screen.getByRole("heading", { name: "Custom empty" })).toBeTruthy();
    expect(screen.queryByText("No rooms")).toBeNull();
  });

  it("selects a room and shows unread badge", () => {
    const onSelect = vi.fn();
    render(
      <RoomInboxList
        classNames={classNames}
        listAriaLabel="Inbox"
        emptyLabel="No rooms"
        unreadBadgeLabel={(n) => `${n} unread`}
        onSelect={onSelect}
        items={[
          {
            id: "r1",
            title: "Pedido 102942",
            preview: "Atualização",
            unreadCount: 2,
            kindLabel: "Entity",
          },
        ]}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Pedido 102942/ }));
    expect(onSelect).toHaveBeenCalledWith("r1");
    expect(screen.getByText("2 unread")).toBeTruthy();
  });

  it("renders leading and subtitle slots", () => {
    render(
      <RoomInboxList
        classNames={classNames}
        listAriaLabel="Inbox"
        emptyLabel="No rooms"
        leading={() => <span>AV</span>}
        subtitle={(item) => `Cliente ${item.title}`}
        items={[
          {
            id: "r1",
            title: "Pedido 102942",
            preview: "Atualização",
            selected: true,
          },
        ]}
      />,
    );
    expect(screen.getByText("AV")).toBeTruthy();
    expect(screen.getByText("Cliente Pedido 102942")).toBeTruthy();
    expect(screen.getByRole("button").getAttribute("aria-current")).toBe("true");
  });


  it("actions click does not select the room", () => {
    const onSelect = vi.fn();
    const onDelete = vi.fn();
    render(
      <RoomInboxList
        classNames={classNames}
        listAriaLabel="Inbox"
        emptyLabel="No rooms"
        onSelect={onSelect}
        actions={() => (
          <button type="button" aria-label="Delete room" onClick={onDelete}>
            Del
          </button>
        )}
        items={[{ id: "r1", title: "Pedido 102942" }]}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Delete room" }));
    expect(onDelete).toHaveBeenCalledTimes(1);
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("o hit da linha cobre o card e o avatar permanece fora do botão", () => {
    const { container } = render(
      <RoomInboxList
        classNames={classNames}
        listAriaLabel="Inbox"
        emptyLabel="No rooms"
        leading={() => (
          <a href="/apps/commercial/customers/1/01" title="Abrir conta de WEG">
            AV
          </a>
        )}
        items={[
          {
            id: "r1",
            title: "Pedido 102942",
          },
        ]}
      />,
    );
    const link = screen.getByRole("link", { name: "AV" });
    const button = screen.getByRole("button", { name: /Pedido 102942/ });
    expect(button.className).toMatch(/delpi-ui-room-inbox__hit/);
    expect(button.contains(link)).toBe(false);
    expect(container.querySelector(".delpi-ui-room-inbox__leading")?.contains(link)).toBe(
      true,
    );
  });
});

describe("room-inbox.css", () => {
  it("seleção usa fill sem barra lateral", () => {
    const css = readFileSync(join(stylesDir, "room-inbox.css"), "utf8");
    const item = css.match(/\.delpi-ui-room-inbox__item \{[^}]+\}/)?.[0] ?? "";
    const selected =
      css.match(/\.delpi-ui-room-inbox__item--selected \{[^}]+\}/)?.[0] ?? "";
    expect(item).toMatch(/position:\s*relative;/);
    expect(item).toMatch(/border:\s*none;/);
    expect(item).not.toMatch(/border:\s*1px solid/);
    expect(selected).toMatch(/box-shadow:\s*none;/);
    expect(selected).not.toMatch(/inset 3px/);
    expect(selected).not.toMatch(/border-color:/);
    const hit = css.match(/\.delpi-ui-room-inbox__hit \{[^}]+\}/)?.[0] ?? "";
    expect(hit).toMatch(/position:\s*absolute;/);
    expect(hit).toMatch(/inset:\s*0;/);
    expect(hit).toMatch(/appearance:\s*none;/);
    const body = css.match(/\.delpi-ui-room-inbox__body \{[^}]+\}/)?.[0] ?? "";
    expect(body).not.toMatch(/appearance:\s*none;/);
    expect(body).toMatch(/flex:\s*1 1 0;/);
    expect(body).toMatch(/width:\s*100%;/);
    expect(body).toMatch(/border:\s*none;/);
    const row = css.match(/\.delpi-ui-room-inbox__row \{[^}]+\}/)?.[0] ?? "";
    expect(row).toMatch(/width:\s*100%;/);
    expect(row).toMatch(/align-items:\s*stretch;/);
    expect(row).toMatch(/pointer-events:\s*none;/);
  });

  it("não reserva coluna de meta vazia na linha", () => {
    const { container } = render(
      <RoomInboxList
        classNames={classNames}
        listAriaLabel="Inbox"
        emptyLabel="No rooms"
        items={[{ id: "r1", title: "BUHLER", kindLabel: "Entidade" }]}
      />,
    );
    expect(container.querySelector(".delpi-ui-room-inbox__meta")).toBeNull();
  });

  it("actions slot is clickable above hit and appears on hover", () => {
    const css = readFileSync(join(stylesDir, "room-inbox.css"), "utf8");
    const actions = css.match(/\.delpi-ui-room-inbox__actions \{[^}]+\}/)?.[0] ?? "";
    expect(actions).toMatch(/pointer-events:\s*auto;/);
    expect(actions).toMatch(/opacity:\s*0;/);
    expect(css).toMatch(/\.delpi-ui-room-inbox__item:hover \.delpi-ui-room-inbox__actions/);
    expect(css).toMatch(/\.delpi-ui-room-inbox__item:focus-within \.delpi-ui-room-inbox__actions/);
  });

  it("lista scrollável sem estourar largura do card", () => {
    const css = readFileSync(join(stylesDir, "room-inbox.css"), "utf8");
    const root = css.match(/\.delpi-ui-room-inbox \{[^}]+\}/)?.[0] ?? "";
    const list = css.match(/\.delpi-ui-room-inbox__list \{[^}]+\}/)?.[0] ?? "";
    const item = css.match(/\.delpi-ui-room-inbox__item \{[^}]+\}/)?.[0] ?? "";
    expect(root).toMatch(/overflow:\s*hidden/);
    expect(root).not.toMatch(/height:\s*100%/);
    expect(list).toMatch(/overflow-y:\s*auto/);
    expect(list).toMatch(/overscroll-behavior:\s*contain/);
    expect(list).not.toMatch(/overflow-x:\s*hidden/);
    expect(list).toMatch(/scrollbar-gutter:\s*stable/);
    expect(item).toMatch(/max-width:\s*100%/);
    expect(css).toMatch(/\.delpi-ui-room-inbox__list > li \{[\s\S]*?max-width:\s*100%/);
  });

  it("painel contém o scroll da listagem sem chrome visual", () => {
    const css = readFileSync(join(stylesDir, "room-inbox.css"), "utf8");
    const panel = css.match(/\.delpi-ui-room-inbox-panel \{[^}]+\}/)?.[0] ?? "";
    expect(panel).toMatch(/overflow:\s*hidden/);
    expect(panel).toMatch(/min-height:\s*0/);
    expect(panel).toMatch(/background:\s*transparent/);
    expect(panel).toMatch(/padding:\s*0/);
    expect(panel).toMatch(/border:\s*none/);
    expect(classNames.panel).toMatch(/delpi-ui-room-inbox-panel/);
    const { container } = render(
      <RoomInboxPanel classNames={classNames} aria-label="Salas">
        <span>lista</span>
      </RoomInboxPanel>,
    );
    const el = container.querySelector(".delpi-ui-room-inbox-panel");
    expect(el?.getAttribute("role")).toBe("region");
    expect(el?.getAttribute("aria-label")).toBe("Salas");
  });
});

