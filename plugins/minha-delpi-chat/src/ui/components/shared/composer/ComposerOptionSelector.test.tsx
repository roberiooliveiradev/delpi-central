import { renderToStaticMarkup } from "react-dom/server";
import { Gauge } from "lucide-react";
import { describe, expect, it } from "vitest";

import { ComposerOptionSelector } from "./ComposerOptionSelector";

const OPTIONS = [
  { id: "normal" as const, label: "Normal", description: "Resposta equilibrada" },
  { id: "fast" as const, label: "Rápido", description: "Resposta mais curta" },
];

describe("ComposerOptionSelector", () => {
  it("renderiza gatilho com rótulo ativo e atributos de acessibilidade", () => {
    const html = renderToStaticMarkup(
      <ComposerOptionSelector
        options={OPTIONS}
        value="normal"
        onChange={() => undefined}
        renderIcon={() => <Gauge size={15} aria-hidden="true" />}
        menuLabel="Modo de resposta"
        tourId="composer-response-mode"
      />,
    );

    expect(html).toContain("mdc-composer-option-selector");
    expect(html).toContain("mdc-composer-option-selector__trigger");
    expect(html).toContain("Normal");
    expect(html).toContain('aria-haspopup="listbox"');
    expect(html).toContain('aria-expanded="false"');
    expect(html).toContain('data-tour="composer-response-mode"');
  });

  it("não renderiza quando não há opções", () => {
    const html = renderToStaticMarkup(
      <ComposerOptionSelector
        options={[]}
        value="normal"
        onChange={() => undefined}
        renderIcon={() => null}
        menuLabel="Modo"
      />,
    );

    expect(html).toBe("");
  });
});
