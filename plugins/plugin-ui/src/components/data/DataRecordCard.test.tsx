import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { MouseEvent } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DataRecordCard, dataRecordCardBemClasses } from "./DataRecordCard";

afterEach(cleanup);

const classNames = dataRecordCardBemClasses("cm");

describe("DataRecordCard", () => {
  it("renderiza artigo e campos sem regra de domínio", () => {
    const { container } = render(
      <DataRecordCard
        classNames={classNames}
        title="Pedido 123"
        subtitle="Cliente ACME"
        status={<span>Em análise</span>}
        fields={[
          { id: "value", label: "Valor", value: "R$ 1.250,00" },
          { id: "hidden", label: "Oculto", value: "Não exibir", present: false },
        ]}
        context="Atualizado há 5 min"
        ariaLabel="Resumo do pedido 123"
      />,
    );

    expect(screen.getByRole("article", { name: "Resumo do pedido 123" })).toBeTruthy();
    expect(container.querySelector("dl")).toBeTruthy();
    expect(container.querySelector("dt")?.textContent).toBe("Valor");
    expect(container.querySelector("dd")?.textContent).toBe("R$ 1.250,00");
    expect(screen.queryByText("Oculto")).toBeNull();
    expect(container.querySelector(".cm-data-record-card")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-data-record-card")).toBeTruthy();
  });

  it("usa anchor real quando href é informado", () => {
    const onNavigate = vi.fn((event: MouseEvent<HTMLAnchorElement>) =>
      event.preventDefault(),
    );
    render(
      <DataRecordCard
        classNames={classNames}
        title="Abrir pedido"
        href="/pedidos/123"
        onNavigate={onNavigate}
      />,
    );

    const link = screen.getByRole("link", { name: "Abrir pedido" });
    expect(link.getAttribute("href")).toBe("/pedidos/123");
    fireEvent.click(link);
    expect(onNavigate).toHaveBeenCalledTimes(1);
  });

  it("rejeita href externo ou executável", () => {
    expect(() =>
      render(
        <DataRecordCard
          classNames={classNames}
          title="Perigoso"
          href="data:text/html,alert(1)"
        />,
      ),
    ).toThrow(/não é interno/);
    expect(() =>
      render(
        <DataRecordCard
          classNames={classNames}
          title="Externo"
          href="https://example.com"
        />,
      ),
    ).toThrow(/não é interno/);
  });
});
