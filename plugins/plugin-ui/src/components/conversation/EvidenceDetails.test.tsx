import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { EvidenceDetails } from "./EvidenceDetails";

afterEach(cleanup);

const ITEMS = [
  { label: "Classificação", value: "OBSERVATION" },
  { label: "Fonte", value: "Cadastro DELPI" },
  { label: "Especialista", value: "DAVI" },
  { label: "Observado em", value: "16/10/2026 14:32" },
];

describe("EvidenceDetails", () => {
  it("renders only the source summary when there are no details", () => {
    render(<EvidenceDetails sourceSummary="Fonte · Cadastro DELPI" />);
    expect(screen.getByText("Fonte · Cadastro DELPI")).toBeTruthy();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("keeps the detail region closed by default", () => {
    render(
      <EvidenceDetails sourceSummary="Fonte" items={ITEMS} />,
    );
    const region = document.querySelector(
      ".delpi-ui-evidence-details__detail",
    );
    expect(region?.hasAttribute("hidden")).toBe(true);
    const trigger = screen.getByRole("button", {
      name: /Detalhes da evidência/,
    });
    expect(trigger.getAttribute("aria-expanded")).toBe("false");
  });

  it("opens the disclosure and renders dl/dt/dd pairs", () => {
    render(
      <EvidenceDetails sourceSummary="Fonte" items={ITEMS} />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: /Detalhes da evidência/ }),
    );
    const region = document.querySelector(
      ".delpi-ui-evidence-details__detail",
    );
    expect(region?.hasAttribute("hidden")).toBe(false);
    expect(region?.querySelector("dl")).toBeTruthy();
    expect(screen.getByText("OBSERVATION")).toBeTruthy();
    expect(screen.getByText("DAVI")).toBeTruthy();
  });

  it("supports keyboard disclosure", () => {
    render(<EvidenceDetails items={ITEMS} />);
    const trigger = screen.getByRole("button");
    trigger.focus();
    fireEvent.keyDown(trigger, { key: "Enter" });
    fireEvent.click(trigger);
    expect(trigger.getAttribute("aria-expanded")).toBe("true");
  });

  it("renders limitations verbatim", () => {
    render(
      <EvidenceDetails
        items={ITEMS}
        limitations={["Dados sujeitos ao horário da última atualização."]}
      />,
    );
    fireEvent.click(screen.getByRole("button"));
    expect(
      screen.getByText("Dados sujeitos ao horário da última atualização."),
    ).toBeTruthy();
    expect(screen.getByText("Limitações")).toBeTruthy();
  });

  it("shows material limitation only when explicitly supplied", () => {
    render(
      <EvidenceDetails
        items={ITEMS}
        limitations={["lim"]}
        materialLimitationLabel="Há limitações nesta resposta"
      />,
    );
    expect(
      screen.getByText("Há limitações nesta resposta"),
    ).toBeTruthy();
    // and the trigger stays closed
    expect(
      screen.getByRole("button").getAttribute("aria-expanded"),
    ).toBe("false");
  });

  it("never invents a material warning from limitations alone", () => {
    const { container } = render(
      <EvidenceDetails items={ITEMS} limitations={["lim"]} />,
    );
    expect(
      container.querySelector(".delpi-ui-evidence-details__material"),
    ).toBeNull();
    expect(screen.queryByText(/limitações nesta resposta/i)).toBeNull();
  });

  it("renders epistemic class literally — no badge semantics", () => {
    render(<EvidenceDetails items={ITEMS} defaultExpanded />);
    const value = screen.getByText("OBSERVATION");
    expect(value.tagName).toBe("DD");
    // No success/status badge, no tone class on the item.
    expect(value.className).toBe(
      "delpi-ui-evidence-details__item-value",
    );
  });

  it("renders hostile text as inert text", () => {
    render(
      <EvidenceDetails
        sourceSummary={'<img src=x onerror="alert(1)">'}
        items={[{ label: "l", value: '<b onmouseover="x()">v</b>' }]}
        defaultExpanded
      />,
    );
    expect(document.querySelector("img")).toBeNull();
    expect(
      screen.getByText('<img src=x onerror="alert(1)">'),
    ).toBeTruthy();
  });

  it("does not use role=alert or role=status", () => {
    const { container } = render(
      <EvidenceDetails
        sourceSummary="Fonte"
        items={ITEMS}
        limitations={["lim"]}
        materialLimitationLabel="material"
        defaultExpanded
      />,
    );
    expect(container.querySelector('[role="alert"]')).toBeNull();
    expect(container.querySelector('[role="status"]')).toBeNull();
  });

  it("honours className and custom labels", () => {
    const { container } = render(
      <EvidenceDetails
        items={ITEMS}
        disclosureLabel="Ver evidência"
        limitationsLabel="Ressalvas"
        limitations={["x"]}
        className="mine"
      />,
    );
    expect(
      container.querySelector(".delpi-ui-evidence-details.mine"),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: /Ver evidência/ }),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByText("Ressalvas")).toBeTruthy();
  });
});
