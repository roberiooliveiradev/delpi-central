import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ComunicadoBlockView } from "./comunicadoBlockView";
import { createShapeBlock } from "./comunicadoHelpers";

afterEach(cleanup);

describe("ComunicadoBlockView", () => {
  it("não reaplica a rotação no conteúdo quando o host controla o transform", () => {
    const block = {
      ...createShapeBlock("roundRect"),
      style: { rotation: 37 },
    };
    const { container } = render(
      <ComunicadoBlockView block={block} embedded interactive />,
    );

    const content = container.querySelector<HTMLElement>(
      ".tdp-comunicado__block--shape",
    );
    expect(content?.style.transform).toBe("");
    expect(content?.style.transformOrigin).toBe("");
  });

  it("mantém a rotação na apresentação não embutida", () => {
    const block = {
      ...createShapeBlock("roundRect"),
      style: { rotation: 37 },
    };
    const { container } = render(<ComunicadoBlockView block={block} />);

    expect(
      container.querySelector<HTMLElement>(".tdp-comunicado__block--shape")
        ?.style.transform,
    ).toContain("rotate(37deg)");
  });
});
