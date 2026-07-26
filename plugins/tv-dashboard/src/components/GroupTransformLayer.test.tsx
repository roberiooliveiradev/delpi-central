import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { beginGroupGesture, applyGroupRotate } from "../utils/stageGroupGesture";
import { GroupTransformLayer } from "./GroupTransformLayer";

afterEach(cleanup);

function member(
  id: string,
  frame: { x: number; y: number; w: number; h: number },
): ComunicadoBlock {
  return {
    id,
    type: "shape",
    shape: "rectangle",
    frame,
    style: { rotation: 0 },
  } as ComunicadoBlock;
}

describe("GroupTransformLayer", () => {
  it("aplica o giro uma vez no pai e mantém membros sem giro próprio", () => {
    const members = [
      member("a", { x: 10, y: 20, w: 20, h: 15 }),
      member("b", { x: 45, y: 25, w: 25, h: 20 }),
    ];
    const start = beginGroupGesture({
      members: members.map((block) => ({
        id: block.id,
        frame: block.frame,
        rotation: block.style?.rotation ?? 0,
      })),
      slideAspect: 16 / 9,
    });
    const gesture = applyGroupRotate(start!, 35);
    const { container } = render(
      <GroupTransformLayer
        gesture={gesture}
        members={members}
        renderMember={({ block, wrapStyle }) => (
          <div data-testid={`member-${block.id}`} style={wrapStyle} />
        )}
      />,
    );

    const layer = container.querySelector<HTMLElement>("[data-group-layer]");
    const renderedMembers = [
      container.querySelector<HTMLElement>('[data-testid="member-a"]'),
      container.querySelector<HTMLElement>('[data-testid="member-b"]'),
    ];

    expect(layer?.style.transform).toBe("rotate(35deg)");
    for (const rendered of renderedMembers) {
      expect(rendered?.style.transform).toBe("");
      expect(rendered?.style.position).toBe("absolute");
    }
  });

  it("preserva apenas a rotação local pré-existente no membro", () => {
    const members = [
      {
        ...member("a", { x: 10, y: 20, w: 20, h: 15 }),
        style: { rotation: 10 },
      } as ComunicadoBlock,
      member("b", { x: 45, y: 25, w: 25, h: 20 }),
    ];
    const start = beginGroupGesture({
      members: members.map((block) => ({
        id: block.id,
        frame: block.frame,
        rotation: block.style?.rotation ?? 0,
      })),
      slideAspect: 16 / 9,
    });
    const gesture = applyGroupRotate(start!, 30);
    const { container } = render(
      <GroupTransformLayer
        gesture={gesture}
        members={members}
        renderMember={({ block, wrapStyle }) => (
          <div data-testid={`member-${block.id}`} style={wrapStyle} />
        )}
      />,
    );

    expect(
      container.querySelector<HTMLElement>("[data-group-layer]")?.style.transform,
    ).toBe("rotate(30deg)");
    /* O membro A conserva só seus 10° locais; não recebe 30° novamente. */
    expect(
      container.querySelector<HTMLElement>('[data-testid="member-a"]')?.style.transform,
    ).toBe("rotate(10deg)");
    expect(
      container.querySelector<HTMLElement>('[data-testid="member-b"]')?.style.transform,
    ).toBe("");
  });
});
