import { cleanup, render, screen } from "@testing-library/react";
import { MessageSquare } from "lucide-react";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";

import {
  EmptyGuidance,
  emptyGuidanceBemClasses,
} from "./EmptyGuidance";

const classNames = emptyGuidanceBemClasses("test");
const stylesDir = join(import.meta.dirname, "../../styles");

afterEach(() => {
  cleanup();
});

describe("EmptyGuidance", () => {
  it("renders panel variant with title and message", () => {
    render(
      <EmptyGuidance
        variant="panel"
        title="Nenhuma conversa"
        message="Inicie um chat com sua equipe."
        classNames={classNames}
      />,
    );
    expect(screen.getByRole("heading", { level: 3, name: "Nenhuma conversa" })).toBeTruthy();
    expect(screen.getByText("Inicie um chat com sua equipe.")).toBeTruthy();
  });

  it("renders canvas variant with icon and actions", () => {
    render(
      <EmptyGuidance
        variant="canvas"
        title="Selecione uma conversa"
        message="Escolha na lista ao lado."
        icon={<MessageSquare data-testid="icon" />}
        classNames={classNames}
      >
        <button type="button">Nova sala</button>
      </EmptyGuidance>,
    );
    expect(screen.getByText("Selecione uma conversa")).toBeTruthy();
    expect(screen.getByTestId("icon")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Nova sala" })).toBeTruthy();
  });

  it("exports canonical BEM classes", () => {
    expect(classNames.rootPanel).toMatch(/delpi-ui-empty-guidance--panel/);
    expect(classNames.rootCanvas).toMatch(/delpi-ui-empty-guidance--canvas/);
  });

  it("ships panel and canvas layout rules", () => {
    const css = readFileSync(join(stylesDir, "empty-guidance.css"), "utf8");
    expect(css).toMatch(/\.delpi-ui-empty-guidance--panel/);
    expect(css).toMatch(/\.delpi-ui-empty-guidance--canvas/);
    expect(css).toMatch(/pointer-events: auto/);
  });
});
