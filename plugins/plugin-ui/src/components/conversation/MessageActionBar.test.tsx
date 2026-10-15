import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { IconButton } from "../actions/IconButton";
import { MessageActionBar } from "./MessageActionBar";

afterEach(cleanup);

describe("MessageActionBar", () => {
  it("renders children actions", () => {
    render(
      <MessageActionBar>
        <IconButton aria-label="Copiar">c</IconButton>
      </MessageActionBar>,
    );
    expect(document.querySelector(".delpi-ui-message-action-bar")).toBeTruthy();
    expect(
      document.querySelector('.delpi-ui-message-action-bar button[aria-label="Copiar"]'),
    ).toBeTruthy();
  });

  it("defaults to hover-focus visibility and end alignment", () => {
    const { container } = render(
      <MessageActionBar>
        <IconButton aria-label="a">a</IconButton>
      </MessageActionBar>,
    );
    const bar = container.querySelector(".delpi-ui-message-action-bar")!;
    expect(bar.classList.contains("delpi-ui-message-action-bar--hover-focus")).toBe(true);
    expect(bar.classList.contains("delpi-ui-message-action-bar--start")).toBe(false);
  });

  it("supports always visibility, compact density and start align", () => {
    const { container } = render(
      <MessageActionBar visibility="always" density="compact" align="start">
        <IconButton aria-label="a">a</IconButton>
      </MessageActionBar>,
    );
    const bar = container.querySelector(".delpi-ui-message-action-bar")!;
    expect(bar.classList.contains("delpi-ui-message-action-bar--always")).toBe(true);
    expect(bar.classList.contains("delpi-ui-message-action-bar--compact")).toBe(true);
    expect(bar.classList.contains("delpi-ui-message-action-bar--start")).toBe(true);
  });

  it("applies className and group accessible name only when provided", () => {
    const { container } = render(
      <MessageActionBar className="x" aria-label="Ações da resposta">
        <IconButton aria-label="a">a</IconButton>
      </MessageActionBar>,
    );
    const bar = container.querySelector(".delpi-ui-message-action-bar")!;
    expect(bar.getAttribute("role")).toBe("group");
    expect(bar.getAttribute("aria-label")).toBe("Ações da resposta");
    expect(bar.classList.contains("x")).toBe(true);
  });

  it("omits role=group when no label is provided", () => {
    const { container } = render(
      <MessageActionBar>
        <IconButton aria-label="a">a</IconButton>
      </MessageActionBar>,
    );
    expect(
      container.querySelector(".delpi-ui-message-action-bar")!.getAttribute("role"),
    ).toBeNull();
  });
});
