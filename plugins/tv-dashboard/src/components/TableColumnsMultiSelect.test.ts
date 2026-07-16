import { describe, expect, it } from "vitest";

import {
  moveTableColumn,
  patchTableColumnVisibility,
  resolveVisibleKeys,
} from "./TableColumnsMultiSelect";

const options = [
  { key: "a", label: "A" },
  { key: "b", label: "B" },
  { key: "c", label: "C" },
];

describe("TableColumnsMultiSelect helpers", () => {
  it("resolveVisibleKeys usa catálogo quando sem projeção", () => {
    expect(resolveVisibleKeys(options)).toEqual(["a", "b", "c"]);
  });

  it("oculta coluna e mantém ordem", () => {
    const next = patchTableColumnVisibility(options, ["a", "b", "c"], "b", false);
    expect(next?.columns?.filter((col) => col.visible).map((col) => col.key)).toEqual(["a", "c"]);
  });

  it("reordena coluna visível", () => {
    const projection = patchTableColumnVisibility(options, ["a", "b", "c"], "c", false);
    const moved = moveTableColumn(options, projection, "a", 1);
    expect(moved?.columns?.filter((col) => col.visible).map((col) => col.key)).toEqual(["b", "a"]);
  });
});
