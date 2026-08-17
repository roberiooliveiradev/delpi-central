import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { ChatSelectionPendingPanel } from "./ChatSelectionPendingPanel";

describe("ChatSelectionPendingPanel", () => {
  it("renderiza candidatos e CTA de confirmação", () => {
    const html = renderToStaticMarkup(
      <ChatSelectionPendingPanel
        pending={{
          kind: "catalog_route",
          multiSelect: true,
          prompt: "Selecione as fontes",
          confirmLabel: "Adicionar selecionadas",
          cancelLabel: "Cancelar",
          candidates: [
            {
              id: "op_a",
              label: "Fonte A",
              operationId: "op_a",
              reason: "melhor match",
              evidence: {
                shape: "table",
                columns: ["filial", "valor"],
                rows: [["01", "10"]],
              },
            },
            {
              id: "op_b",
              label: "Fonte B",
              operationId: "op_b",
            },
          ],
        }}
        onUseQuery={() => undefined}
      />,
    );

    expect(html).toContain("mdc-chat-selection-pending");
    expect(html).toContain("Selecione as fontes");
    expect(html).toContain("Fonte A");
    expect(html).toContain("Fonte B");
    expect(html).toContain("Adicionar selecionadas");
    expect(html).toContain("filial");
    expect(html).toContain("melhor match");
  });

  it("não renderiza sem candidatos ou sem callback", () => {
    const empty = renderToStaticMarkup(
      <ChatSelectionPendingPanel
        pending={{ candidates: [] }}
        onUseQuery={() => undefined}
      />,
    );
    expect(empty).toBe("");

    const noCb = renderToStaticMarkup(
      <ChatSelectionPendingPanel
        pending={{
          candidates: [{ id: "x", label: "X" }],
        }}
      />,
    );
    expect(noCb).toBe("");
  });
});
