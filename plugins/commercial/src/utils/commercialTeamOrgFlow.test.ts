import { describe, expect, it } from "vitest";

import { buildCommercialGroupsOrgFlowModel } from "./commercialTeamOrgFlow";

describe("buildCommercialGroupsOrgFlowModel", () => {
  it("liga grupo → pessoa sem nós portfolio", () => {
    const model = buildCommercialGroupsOrgFlowModel({
      people: [
        {
          user_id: "u-ana",
          name: "Ana",
          email: "ana@ex.com",
          groups: [{ id: "g1", name: "Inside", active: true }],
        },
        {
          user_id: "u-bia",
          name: "Bia",
          groups: [
            { id: "g1", name: "Inside", active: true },
            { id: "g2", name: "Field", active: false },
          ],
        },
        {
          user_id: "u-solo",
          name: "Solo",
          groups: [],
        },
      ],
    });

    expect(model.nodes.some((node) => node.kind === "portfolio")).toBe(false);
    expect(model.nodes.filter((node) => node.kind === "group")).toHaveLength(2);
    expect(model.nodes.filter((node) => node.kind === "person")).toHaveLength(3);
    expect(model.edges).toEqual(
      expect.arrayContaining([
        { id: "edge:g1:u-ana", source: "group:g1", target: "person:u-ana" },
        { id: "edge:g1:u-bia", source: "group:g1", target: "person:u-bia" },
        { id: "edge:g2:u-bia", source: "group:g2", target: "person:u-bia" },
      ]),
    );
  });

  it("nunca usa user_id como título da pessoa", () => {
    const uuid = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee";
    const model = buildCommercialGroupsOrgFlowModel({
      people: [
        {
          user_id: uuid,
          name: uuid,
          groups: [{ id: "g1", name: "Inside", active: true }],
        },
      ],
    });
    const person = model.nodes.find((node) => node.kind === "person");
    expect(person?.title).toBe("Usuário");
    expect(person?.title).not.toBe(uuid);
  });
});
