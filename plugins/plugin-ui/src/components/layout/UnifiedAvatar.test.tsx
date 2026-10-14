import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { UnifiedAvatar, isSafeAvatarImageUrl } from "./UnifiedAvatar";

afterEach(cleanup);

describe("UnifiedAvatar", () => {
  it.each(["xs", "sm", "md", "lg", "xl"] as const)("renders assistant size %s", (size) => {
    const { container } = render(<UnifiedAvatar kind="assistant" label="DÉLIA" size={size} />);
    expect(container.querySelector(".delpi-ui-unified-avatar--" + size)).toBeTruthy();
    expect(screen.getByRole("img", { name: "DÉLIA" })).toBeTruthy();
  });

  it("is idle by default; only explicit live state activates processing", () => {
    const { container, rerender } = render(<UnifiedAvatar kind="assistant" label="DÉLIA" />);
    expect(container.querySelector('[data-motion="idle"]')).toBeTruthy();
    rerender(<UnifiedAvatar kind="assistant" label="DÉLIA" motionState="processing" />);
    expect(container.querySelector('[data-motion="processing"]')).toBeTruthy();
    rerender(<UnifiedAvatar kind="assistant" label="DÉLIA" motionState="idle" />);
    expect(container.querySelector('[data-motion="processing"]')).toBeNull();
  });

  it("uses a neutral person fallback when no published identity is provided", () => {
    const { container } = render(<UnifiedAvatar kind="person" label="Você" />);
    expect(screen.getByRole("img", { name: "Você" })).toBeTruthy();
    expect(container.querySelector("svg")).toBeTruthy();
    expect(container.querySelector("button")).toBeNull();
    expect(container.querySelector("img")).toBeNull();
  });

  it("renders authorized initials and recovers from a broken photo", () => {
    const { container, rerender } = render(
      <UnifiedAvatar kind="person" label="Usuário" fallbackText="Ana Silva" imageUrl="/photos/1" />,
    );
    fireEvent.error(container.querySelector("img")!);
    expect(container.querySelector("img")).toBeNull();
    expect(container.textContent).toContain("AS");
    rerender(<UnifiedAvatar kind="person" label="Usuário" fallbackText="Ana Silva" imageUrl="/photos/2" />);
    expect(container.querySelector("img")?.getAttribute("src")).toBe("/photos/2");
  });

  it("rejects executable image URLs", () => {
    expect(isSafeAvatarImageUrl("javascript:alert(1)")).toBe(false);
    expect(isSafeAvatarImageUrl("data:image/svg+xml,hello")).toBe(false);
    expect(isSafeAvatarImageUrl("//example.test/photo")).toBe(false);
    expect(isSafeAvatarImageUrl("/photo")).toBe(true);
    const { container } = render(<UnifiedAvatar kind="person" label="Você" imageUrl="javascript:alert(1)" />);
    expect(container.querySelector("img")).toBeNull();
  });
});
