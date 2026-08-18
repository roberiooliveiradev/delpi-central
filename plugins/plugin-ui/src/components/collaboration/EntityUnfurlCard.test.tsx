import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { EntityUnfurlCard, entityUnfurlCardBemClasses } from "./EntityUnfurlCard";

const classNames = entityUnfurlCardBemClasses("test");

afterEach(() => {
  cleanup();
});

describe("EntityUnfurlCard", () => {
  it("renders fields when accessible", () => {
    render(
      <EntityUnfurlCard
        classNames={classNames}
        title="Pedido 102942"
        kindLabel="Order"
        fields={[{ id: "customer", label: "Customer", value: "ACME" }]}
        openLabel="Open"
        onOpen={vi.fn()}
      />,
    );
    expect(screen.getByText("Pedido 102942")).toBeTruthy();
    expect(screen.getByText("ACME")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Open" })).toBeTruthy();
  });

  it("shows denied copy without fields or open action", () => {
    const onOpen = vi.fn();
    const { container } = render(
      <EntityUnfurlCard
        classNames={classNames}
        title="Pedido 102942"
        accessible={false}
        deniedLabel="No access"
        openLabel="Open"
        onOpen={onOpen}
      />,
    );
    expect(screen.getByText("No access")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Open" })).toBeNull();
    expect(container.querySelector(".delpi-ui-entity-unfurl--denied")).not.toBeNull();
  });

  it("fires onOpen", () => {
    const onOpen = vi.fn();
    render(
      <EntityUnfurlCard
        classNames={classNames}
        title="X"
        openLabel="Open"
        onOpen={onOpen}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    expect(onOpen).toHaveBeenCalledTimes(1);
  });
});
