import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RoomContextPanel, roomContextPanelBemClasses } from "./RoomContextPanel";

const classNames = roomContextPanelBemClasses("test");
const labels = {
  about: "About",
  participants: "Participants",
  pins: "Pinned",
  pinsEmpty: "No pins",
  membersEmpty: "Nobody listed",
  openEntity: "Open",
};

afterEach(() => {
  cleanup();
});

describe("RoomContextPanel", () => {
  it("renders empty members and pins", () => {
    render(
      <RoomContextPanel
        classNames={classNames}
        labels={labels}
        entityTitle="Order"
        entityKey="01|002573"
      />,
    );
    expect(screen.getByRole("heading", { name: "About" })).toBeTruthy();
    expect(screen.getByText("Nobody listed")).toBeTruthy();
    expect(screen.getByText("No pins")).toBeTruthy();
    expect(screen.queryByRole("link", { name: /Open/ })).toBeNull();
  });

  it("renders structured ABOUT without raw entity_key", () => {
    render(
      <RoomContextPanel
        classNames={classNames}
        labels={labels}
        entityPrimary="002573"
        entityFields={[
          { label: "Pedido", value: "002573" },
          { label: "Unidade", value: "Espírito Santo" },
        ]}
        entityTitle="Pedido 002573"
        entityKey="02|002573"
        entityHref="/orders/1"
      />,
    );
    expect(screen.getByText("Espírito Santo")).toBeTruthy();
    expect(screen.queryByText("02|002573")).toBeNull();
    expect(screen.getByRole("link", { name: /Open/ })).toBeTruthy();
  });

  it("opens entity link and selects a pin", () => {
    const onOpenEntity = vi.fn();
    const onPinSelect = vi.fn();
    render(
      <RoomContextPanel
        classNames={classNames}
        labels={labels}
        entityTitle="Order"
        entityKey="01|002573"
        entityHref="/orders/1"
        onOpenEntity={onOpenEntity}
        pins={[
          { id: "p1", messageId: "m1", title: "Follow up", dateLabel: "18/08" },
        ]}
        onPinSelect={onPinSelect}
      />,
    );
    fireEvent.click(screen.getByRole("link", { name: /Open/ }));
    expect(onOpenEntity).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: /Follow up/ }));
    expect(onPinSelect).toHaveBeenCalledWith("m1");
  });

  it("aplica o modificador embedded no root", () => {
    const { container } = render(
      <RoomContextPanel
        classNames={classNames}
        labels={labels}
        embedded
        entityTitle="Order"
      />,
    );
    const aside = container.querySelector("aside");
    expect(aside?.className).toMatch(/delpi-ui-room-context-panel--embedded/);
  });

  it("aplica o modificador flush no root", () => {
    const { container } = render(
      <RoomContextPanel
        classNames={classNames}
        labels={labels}
        flush
        entityTitle="Order"
      />,
    );
    const aside = container.querySelector("aside");
    expect(aside?.className).toMatch(/delpi-ui-room-context-panel--flush/);
  });
});
