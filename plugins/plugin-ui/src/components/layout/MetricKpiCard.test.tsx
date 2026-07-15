import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { MetricKpiCard, metricKpiCardBemClasses } from "./MetricKpiCard";

afterEach(() => {
  cleanup();
});

describe("MetricKpiCard", () => {
  it("emite dual-class delpi-ui e body separado", () => {
    const classNames = metricKpiCardBemClasses("pac");
    render(
      <MetricKpiCard
        label="Planos abertos"
        value="12"
        icon={<span data-testid="icon">!</span>}
        classNames={classNames}
        tone="warning"
      />,
    );

    const article = document.querySelector("article");
    expect(article?.className).toContain("delpi-ui-card");
    expect(article?.className).toContain("delpi-ui-kpi-card");
    expect(article?.className).toContain("delpi-ui-kpi-card--warning");
    expect(document.querySelector(".delpi-ui-kpi-header")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-kpi-card__body")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-kpi-icon")).toBeTruthy();
    expect(screen.getByText("Planos abertos")).toBeTruthy();
    expect(screen.getByText("12")).toBeTruthy();
  });
});
