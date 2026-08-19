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
});
