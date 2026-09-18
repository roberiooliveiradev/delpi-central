import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  EntityAvatarLabel,
  entityAvatarLabelBemClasses,
} from "./EntityAvatarLabel";

const classNames = entityAvatarLabelBemClasses("pva");

afterEach(() => {
  cleanup();
});

describe("EntityAvatarLabel", () => {
  it("renders initials and name", () => {
    render(
      <EntityAvatarLabel name="Multiprint" colorKey="000123" classNames={classNames} />,
    );
    expect(screen.getByText("Multiprint")).toBeTruthy();
    expect(screen.getByText("MU")).toBeTruthy();
  });

  it("shows secondary code when it differs from the name", () => {
    render(
      <EntityAvatarLabel
        name="João Silva"
        secondary="JOSI"
        classNames={classNames}
      />,
    );
    expect(screen.getByText("João Silva")).toBeTruthy();
    expect(screen.getByText("JOSI")).toBeTruthy();
  });

  it("returns empty label without identity", () => {
    render(<EntityAvatarLabel name="" classNames={classNames} emptyLabel="—" />);
    expect(screen.getByText("—")).toBeTruthy();
  });

  it("does not repeat secondary when it equals the name", () => {
    const { container } = render(
      <EntityAvatarLabel name="000123" secondary="000123" classNames={classNames} />,
    );
    expect(container.querySelector(".pva-entity-avatar-label__secondary")).toBeNull();
  });
});

describe("entity-avatar-label.css", () => {
  it("styles only the canonical delpi-ui classes", () => {
    const css = readFileSync(
      join(dirname(fileURLToPath(import.meta.url)), "../../styles/entity-avatar-label.css"),
      "utf8",
    );
    expect(css).toMatch(/\.delpi-ui-entity-avatar-label\b/);
    expect(css).not.toMatch(/\[class\*=/);
  });
});
