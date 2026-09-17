import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App shell", () => {
  it("renders accessible product landmark and heading", () => {
    render(
      <App
        pathname="/apps/delia"
        routeLabel="DÉLIA"
        permissions={["should.not.authorize"]}
        isSuperadmin={true}
      />,
    );

    const main = screen.getByRole("main", { name: "DÉLIA" });
    expect(main).toBeTruthy();
    expect(screen.getByRole("heading", { name: "DÉLIA" })).toBeTruthy();
    expect(main.querySelector("[autofocus]")).toBeNull();
  });

  it("accepts host permission props without treating them as backend authority", () => {
    const { container } = render(
      <App permissions={["admin.destroy.everything"]} isSuperadmin={true} />,
    );

    // Presentation shell only — no authorization decision UI or gate based on props.
    expect(container.textContent).not.toMatch(/admin\.destroy\.everything/);
    expect(container.textContent).not.toMatch(/superadmin/i);
    expect(container.querySelector("[data-authorized]")).toBeNull();
    expect(container.querySelector("[data-permission-gate]")).toBeNull();
  });

  it("uses container-friendly responsive foundation classes", () => {
    const { container } = render(<App />);
    const root = container.querySelector(".dashboard-delia");
    expect(root).not.toBeNull();
    expect(root?.classList.contains("dashboard-page")).toBe(true);
    const stack = container.querySelector(".delia-page-stack");
    expect(stack).not.toBeNull();
  });
});
