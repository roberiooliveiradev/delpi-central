import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { RoomHeader, roomHeaderBemClasses } from "./RoomHeader";

const classNames = roomHeaderBemClasses("test");

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
});
