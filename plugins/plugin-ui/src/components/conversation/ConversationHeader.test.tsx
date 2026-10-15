import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ConversationHeader } from "./ConversationHeader";

afterEach(cleanup);

describe("ConversationHeader", () => {
  it("renders title as h1 by default", () => {
    render(<ConversationHeader title="DÉLIA" />);
    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading.textContent).toBe("DÉLIA");
    expect(
      heading.classList.contains("delpi-ui-conversation-header__title"),
    ).toBe(true);
  });

  it("supports a different heading element for embedded use", () => {
    render(<ConversationHeader title="DÉLIA" titleAs="h2" />);
    expect(screen.getByRole("heading", { level: 2 })).toBeTruthy();
    expect(screen.queryByRole("heading", { level: 1 })).toBeNull();
  });

  it("renders optional subtitle, leading and actions", () => {
    const { container } = render(
      <ConversationHeader
        title="DÉLIA"
        subtitle="Inteligência operacional DELPI"
        leading={<span data-testid="lead" />}
        actions={<button type="button">Ação</button>}
      />,
    );
    expect(
      screen.getByText("Inteligência operacional DELPI"),
    ).toBeTruthy();
    expect(
      container.querySelector(".delpi-ui-conversation-header__leading"),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Ação" }),
    ).toBeTruthy();
  });

  it("omits optional regions without placeholders", () => {
    const { container } = render(<ConversationHeader title="DÉLIA" />);
    expect(
      container.querySelector(".delpi-ui-conversation-header__leading"),
    ).toBeNull();
    expect(
      container.querySelector(".delpi-ui-conversation-header__subtitle"),
    ).toBeNull();
    expect(
      container.querySelector(".delpi-ui-conversation-header__actions"),
    ).toBeNull();
  });

  it("applies compact modifier and className", () => {
    const { container } = render(
      <ConversationHeader title="DÉLIA" compact className="app-hdr" />,
    );
    const root = container.querySelector(".delpi-ui-conversation-header");
    expect(
      root?.classList.contains("delpi-ui-conversation-header--compact"),
    ).toBe(true);
    expect(root?.classList.contains("app-hdr")).toBe(true);
  });
});
