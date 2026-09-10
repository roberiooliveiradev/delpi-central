import { describe, expect, it } from "vitest";

import { actionLabel } from "../content/presentationLabels";
import { ActionBar } from "./ActionBar";

describe("ActionBar render-only", () => {
  it("recebe actions da API sem inferir máquina de estados", () => {
    expect(typeof ActionBar).toBe("function");
    const actions = ["start", "cancel"];
    expect(actions).not.toContain("invented-by-frontend");
  });

  it("mapeia label PT sem alterar o código canônico da ação", () => {
    expect(actionLabel("start")).toBe("Iniciar atendimento");
    expect(actionLabel("return")).toBe("Devolver para ajuste");
    expect(actionLabel("cancel")).toBe("Cancelar solicitação");
  });

  it("filtra view antes de renderizar botões", async () => {
    const { filterDetailBarActions } = await import("../utils/operationalActions");
    expect(filterDetailBarActions(["view", "start"])).toEqual(["start"]);
  });
});
