import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ConversationWorkspace } from "./ConversationWorkspace";

afterEach(cleanup);

describe("ConversationWorkspace", () => {
  it("renders header, body and footer regions", () => {
    const { container } = render(
      <ConversationWorkspace
        header={<span>HEADER</span>}
        footer={<span>FOOTER</span>}
        aria-label="Conversa"
      >
        BODY
      </ConversationWorkspace>,
    );
    expect(screen.getByText("HEADER")).toBeTruthy();
    expect(screen.getByText("BODY")).toBeTruthy();
    expect(screen.getByText("FOOTER")).toBeTruthy();
    const root = container.querySelector(
      ".delpi-ui-conversation-workspace",
    );
    expect(root?.getAttribute("aria-label")).toBe("Conversa");
    expect(
      root?.querySelector(".delpi-ui-conversation-workspace__body"),
    ).toBeTruthy();
    expect(
      root?.querySelector(".delpi-ui-conversation-workspace__column"),
    ).toBeTruthy();
  });

  it("omits optional regions when not provided", () => {
    const { container } = render(
      <ConversationWorkspace>BODY</ConversationWorkspace>,
    );
    expect(
      container.querySelector(".delpi-ui-conversation-workspace__header"),
    ).toBeNull();
    expect(
      container.querySelector(".delpi-ui-conversation-workspace__banner"),
    ).toBeNull();
    expect(
      container.querySelector(".delpi-ui-conversation-workspace__footer"),
    ).toBeNull();
  });

  it("renders banner between header and scrollable body", () => {
    const { container } = render(
      <ConversationWorkspace
        header={<span>H</span>}
        banner={<span>SIMULAÇÃO</span>}
        footer={<span>F</span>}
      >
        B
      </ConversationWorkspace>,
    );
    const banner = container.querySelector(
      ".delpi-ui-conversation-workspace__banner",
    );
    const body = container.querySelector(
      ".delpi-ui-conversation-workspace__body",
    );
    expect(banner).toBeTruthy();
    expect(screen.getByText("SIMULAÇÃO")).toBeTruthy();
    // Banner is outside the scroll viewport.
    expect(body?.contains(banner!)).toBe(false);
  });

  it("exposes the scroll viewport through bodyRef and scroll events", () => {
    const bodyRef = { current: null as HTMLDivElement | null };
    const onScroll = vi.fn();
    render(
      <ConversationWorkspace bodyRef={bodyRef} onBodyScroll={onScroll}>
        B
      </ConversationWorkspace>,
    );
    expect(
      bodyRef.current?.classList.contains(
        "delpi-ui-conversation-workspace__body",
      ),
    ).toBe(true);
    fireEvent.scroll(bodyRef.current!);
    expect(onScroll).toHaveBeenCalledTimes(1);
  });

  it("applies density modifier and consumer class names", () => {
    const { container } = render(
      <ConversationWorkspace
        density="compact"
        className="my-app-workspace"
        columnClassName="my-app-column"
      >
        B
      </ConversationWorkspace>,
    );
    const root = container.querySelector(
      ".delpi-ui-conversation-workspace",
    );
    expect(
      root?.classList.contains(
        "delpi-ui-conversation-workspace--compact",
      ),
    ).toBe(true);
    expect(root?.classList.contains("my-app-workspace")).toBe(true);
    expect(
      root
        ?.querySelector(".delpi-ui-conversation-workspace__column")
        ?.classList.contains("my-app-column"),
    ).toBe(true);
  });
});
