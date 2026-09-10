import { describe, expect, it } from "vitest";

import {
  filterDetailBarActions,
  isTransitionAction,
} from "./operationalActions";

describe("operationalActions", () => {
  it("não trata view/edit como transição", () => {
    expect(isTransitionAction("view")).toBe(false);
    expect(isTransitionAction("edit")).toBe(false);
    expect(isTransitionAction("start")).toBe(true);
    expect(isTransitionAction("cancel")).toBe(true);
  });

  it("oculta view na barra do detalhe e preserva demais ações", () => {
    expect(filterDetailBarActions(["view", "start", "cancel", "edit"])).toEqual([
      "start",
      "cancel",
      "edit",
    ]);
  });
});
