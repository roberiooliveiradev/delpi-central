import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RemoteSelectionFrame } from "./RemoteSelectionFrame";

describe("RemoteSelectionFrame", () => {
  it("mostra os nomes únicos dos editores sem capturar interação", () => {
    const { container } = render(
      <RemoteSelectionFrame displayNames={["Ana Silva", "Ana Silva", "Bruno"]} />,
    );
    expect(screen.getByText("Ana Silva, Bruno")).toBeTruthy();
    expect(container.querySelector(".td-composer__remote-selection")).toBeTruthy();
  });

  it("não renderiza sem identidade válida", () => {
    const { container } = render(<RemoteSelectionFrame displayNames={["", "  "]} />);
    expect(container.firstChild).toBeNull();
  });
});

