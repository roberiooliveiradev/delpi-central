import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { SimpleKpiCard, simpleKpiCardBemClasses } from "./SimpleKpiCard";

afterEach(() => {
  cleanup();
});

describe("SimpleKpiCard", () => {
  it("renderiza título, valor e ícone", () => {
    render(
      <SimpleKpiCard
        title="Despesas"
        value="R$ 1.000"
        icon={<span data-testid="icon">$</span>}
        classNames={simpleKpiCardBemClasses("fcc")}
      />,
    );

    expect(screen.getByText("Despesas")).toBeTruthy();
    expect(screen.getByText("R$ 1.000")).toBeTruthy();
    expect(screen.getByTestId("icon")).toBeTruthy();
  });

  it("mostra reticências quando loading", () => {
    render(
      <SimpleKpiCard
        title="Total"
        value="R$ 0"
        loading
        icon={null}
        classNames={simpleKpiCardBemClasses("cr")}
      />,
    );

    expect(screen.getByText("…")).toBeTruthy();
  });
});
