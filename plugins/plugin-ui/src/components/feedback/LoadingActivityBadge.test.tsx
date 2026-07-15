import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  LoadingActivityBadge,
  loadingActivityBadgeBemClasses,
} from "./LoadingActivityBadge";

describe("LoadingActivityBadge", () => {
  it("renderiza label e tone canônico", () => {
    const { container } = render(<LoadingActivityBadge label="Atualizando" tone="info" />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.getAttribute("role")).toBe("status");
    expect(root.textContent).toContain("Atualizando");
    expect(root.className).toContain("delpi-ui-loading-activity-badge--info");
  });

  it("emite dual class com prefixo do plugin", () => {
    const cn = loadingActivityBadgeBemClasses("si");
    const { container } = render(
      <LoadingActivityBadge label="Carregando" tone="neutral" classNames={cn} showBar />,
    );
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).toContain("si-loading-activity-badge");
    expect(root.className).toContain("delpi-ui-loading-activity-badge");
    expect(container.querySelector(".delpi-ui-loading-activity-badge__bar")).toBeTruthy();
    expect(screen.getByText("Carregando")).toBeTruthy();
  });
});
