import { describe, expect, it } from "vitest";

import {
  mapPreviewToUnfurlCardModel,
  shouldUnfurlMentionKind,
} from "./entityUnfurlAdapter";
import { resolveInteractionEntityHref } from "./resolveInteractionEntityHref";

describe("entityUnfurlAdapter", () => {
  it("mapeia preview acessível com fields", () => {
    const model = mapPreviewToUnfurlCardModel({
      kind: "order",
      accessible: true,
      label: "102942",
      subtitle: "01 · ACME",
      hrefStrategy: "order_detail",
      ref: { branch: "01", order: "102942" },
      fields: { status: "aberto" },
    });
    expect(model.accessible).toBe(true);
    expect(model.title).toBe("102942");
    expect(model.kindLabel).toBe("Pedidos");
    expect(model.fields.some((field) => field.value === "01 · ACME")).toBe(true);
    expect(model.fields.some((field) => field.id === "status")).toBe(true);
  });

  it("mapeia preview sem acesso sem vazar fields", () => {
    const model = mapPreviewToUnfurlCardModel({
      kind: "order",
      accessible: false,
      label: "Sem acesso a este registro.",
      hrefStrategy: "order_detail",
      ref: { branch: "01", order: "102942" },
      fields: { value: "secret" },
    });
    expect(model.accessible).toBe(false);
    expect(model.fields).toEqual([]);
    expect(model.deniedLabel).toMatch(/Sem acesso/);
  });

  it("não unfurla menção de usuário", () => {
    expect(shouldUnfurlMentionKind("user")).toBe(false);
    expect(shouldUnfurlMentionKind("order")).toBe(true);
  });
});

describe("resolveInteractionEntityHref", () => {
  it("resolve customer e order paths EN", () => {
    expect(
      resolveInteractionEntityHref("/apps/commercial", "customer_detail", {
        customer_code: "0001",
        customer_store: "01",
      }),
    ).toBe("/apps/commercial/customers/0001/01");

    expect(
      resolveInteractionEntityHref("/apps/commercial", "order_detail", {
        branch: "01",
        order: "102942",
      }),
    ).toBe("/apps/commercial/open-orders/01/102942/001");

    expect(
      resolveInteractionEntityHref("/apps/commercial", "my_day", {
        task_id: "t1",
      }),
    ).toBe("/apps/commercial/my-tasks");
  });

  it("retorna null quando faltam chaves", () => {
    expect(
      resolveInteractionEntityHref("/apps/commercial", "production_order_detail", {
        production_order: "OP1",
        branch: "01",
      }),
    ).toBeNull();
  });
});
