import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { TvDashboardScreenLoading } from "./TvDashboardScreenLoading";

describe("TvDashboardScreenLoading", () => {
  afterEach(() => {
    cleanup();
  });

  it("delega ao ScreenLoading do plugin-ui", () => {
    render(<TvDashboardScreenLoading label="Carregando programação…" />);
    const splash = screen.getByRole("status", { name: "Carregando programação…" });
    expect(splash.className).toContain("delpi-ui-screen-loading");
  });
});
