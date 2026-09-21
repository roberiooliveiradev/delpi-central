import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { DepartmentScoreBadge, departmentScoreBadgeBemClasses } from "./DepartmentScoreBadge";

const CLASS_NAMES = departmentScoreBadgeBemClasses("ds");

afterEach(() => {
  cleanup();
});

describe("DepartmentScoreBadge", () => {
  it("renderiza score e classificação do contrato", () => {
    render(
      <DepartmentScoreBadge
        classNames={CLASS_NAMES}
        scoreLabel="9,40"
        classification="Excelência Integrada"
      />,
    );
    expect(screen.getByText("IDD")).toBeTruthy();
    expect(screen.getByText("9,40")).toBeTruthy();
    expect(screen.getByText("Excelência Integrada")).toBeTruthy();
  });

  it("omite o badge quando o score canônico não existe", () => {
    const { container } = render(
      <DepartmentScoreBadge classNames={CLASS_NAMES} scoreLabel={null} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("não trata 0 como score falso — só renderiza se o contrato enviou o rótulo", () => {
    render(<DepartmentScoreBadge classNames={CLASS_NAMES} scoreLabel="0,00" />);
    expect(screen.getByText("0,00")).toBeTruthy();
  });
});
