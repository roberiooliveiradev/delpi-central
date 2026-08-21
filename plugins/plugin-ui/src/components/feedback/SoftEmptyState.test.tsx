import { cleanup, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it } from "vitest";

import {
  SoftEmptyState,
  softEmptyStateBemClasses,
} from "./SoftEmptyState";

const classNames = softEmptyStateBemClasses("test");
const stylesDir = join(dirname(fileURLToPath(import.meta.url)), "../../styles");

afterEach(() => {
  cleanup();
});

describe("SoftEmptyState", () => {
  it("renderiza ícone, título e mensagem suaves", () => {
    render(
      <SoftEmptyState
        classNames={classNames}
        title="Nenhuma mensagem ainda"
        message="Escreva a primeira mensagem nesta sala."
        icon={<span data-testid="soft-icon">◇</span>}
      />,
    );
    expect(screen.getByRole("status")).toBeTruthy();
    expect(screen.getByText("Nenhuma mensagem ainda")).toBeTruthy();
    expect(screen.getByText("Escreva a primeira mensagem nesta sala.")).toBeTruthy();
    expect(screen.getByTestId("soft-icon")).toBeTruthy();
    expect(classNames.root).toMatch(/delpi-ui-soft-empty/);
  });

  it("CSS soft sem borda de card", () => {
    const css = readFileSync(join(stylesDir, "soft-empty.css"), "utf8");
    const root = css.match(/\.delpi-ui-soft-empty \{[^}]+\}/)?.[0] ?? "";
    expect(root).toMatch(/justify-content:\s*center/);
    expect(root).toMatch(/min-height:\s*100%/);
    expect(root).not.toMatch(/border:/);
    expect(css).toMatch(/\.delpi-ui-soft-empty__icon \{[\s\S]*?opacity:\s*0\.32/);
  });
});
