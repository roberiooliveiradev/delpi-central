// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { MyWegProbableDateShift } from "../types";
import { MyWegProbableDateShiftsSection } from "./MyWegProbableDateShiftsSection";

vi.mock("@delpi/plugin-ui/index", () => ({
  HelpTooltip: () => null,
}));

afterEach(() => {
  cleanup();
});

const shifts: MyWegProbableDateShift[] = [
  {
    productKey: "code:80016354",
    fromRemessa: "2026-11-12",
    toRemessa: "2026-11-10",
    quantityUn: "2",
    kind: "possible_advancement",
    confidence: "probable_not_proven",
  },
  {
    productKey: "code:80016399",
    fromRemessa: "2026-11-01",
    toRemessa: "2026-11-06",
    quantityUn: "10",
    kind: "possible_postponement",
    confidence: "probable_not_proven",
  },
];

describe("MyWegProbableDateShiftsSection", () => {
  it("renderiza antecipação com datas pt-BR, quantidade UN e dias", () => {
    render(<MyWegProbableDateShiftsSection shifts={shifts} resetKey="a|b" />);

    expect(screen.getByText("Possíveis reprogramações de entrega")).toBeTruthy();
    expect(screen.getByText("Resultado considerando o par completo de coletas")).toBeTruthy();
    expect(screen.getByText("80016354")).toBeTruthy();
    expect(screen.getByText("Possível antecipação")).toBeTruthy();
    expect(screen.getByText("12/11/2026")).toBeTruthy();
    expect(screen.getByText("10/11/2026")).toBeTruthy();
    expect(screen.getByText("2 UN")).toBeTruthy();
    expect(screen.getByText("2 dias antes")).toBeTruthy();
    expect(screen.getByText("Possível postergação de 5 dias")).toBeTruthy();
  });

  it("mostra estado vazio sem erro quando não há shifts", () => {
    render(<MyWegProbableDateShiftsSection shifts={undefined} resetKey="empty" />);
    expect(
      screen.getByText("Nenhuma possível reprogramação de data detectada entre as coletas."),
    ).toBeTruthy();
  });

  it("filtra localmente antecipações sem alterar o total do par", () => {
    render(<MyWegProbableDateShiftsSection shifts={shifts} resetKey="filter" />);
    fireEvent.click(screen.getByRole("button", { name: "Antecipações" }));
    expect(screen.getByText("1 de 2 ocorrências")).toBeTruthy();
    expect(screen.getByText("80016354")).toBeTruthy();
    expect(screen.queryByText("80016399")).toBeNull();
  });

  it("marca identidade não confirmada para productKey ref:", () => {
    render(
      <MyWegProbableDateShiftsSection
        resetKey="ref"
        shifts={[
          {
            productKey: "ref:MAT-WEG",
            fromRemessa: "2026-11-12",
            toRemessa: "2026-11-10",
            quantityUn: "1",
            kind: "possible_advancement",
            confidence: "probable_not_proven",
          },
        ]}
      />,
    );
    expect(screen.getByText("MAT-WEG")).toBeTruthy();
    expect(screen.getByText("código não confirmado")).toBeTruthy();
  });
});
