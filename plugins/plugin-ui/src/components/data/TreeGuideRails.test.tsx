import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TreeGuideRails } from "./TreeGuideRails";

describe("TreeGuideRails", () => {
  it("não renderiza na raiz (depth 0)", () => {
    const { container } = render(<TreeGuideRails depth={0} />);
    expect(container.firstChild).toBeNull();
  });

  it("renderiza canto no último irmão do nível atual", () => {
    const { container } = render(
      <TreeGuideRails depth={2} isLastSiblingPath={[false, true]} />
    );
    const slots = container.querySelectorAll(".delpi-ui-tree-guides__slot");
    expect(slots).toHaveLength(2);
    expect(slots[0]?.className).toContain("delpi-ui-tree-guides__slot--vline");
    expect(slots[1]?.className).toContain("delpi-ui-tree-guides__slot--corner");
  });

  it("renderiza tee quando ainda há irmãos abaixo no ramo", () => {
    const { container } = render(
      <TreeGuideRails depth={1} isLastSiblingPath={[false]} />
    );
    const slot = container.querySelector(".delpi-ui-tree-guides__slot");
    expect(slot?.className).toContain("delpi-ui-tree-guides__slot--tee");
  });

  it("usa blank para ancestral que era o último irmão", () => {
    const { container } = render(
      <TreeGuideRails depth={2} isLastSiblingPath={[true, false]} />
    );
    const slots = container.querySelectorAll(".delpi-ui-tree-guides__slot");
    expect(slots[0]?.className).toContain("delpi-ui-tree-guides__slot--blank");
    expect(slots[1]?.className).toContain("delpi-ui-tree-guides__slot--tee");
  });
});
