import { describe, expect, it } from "vitest";

import { createPath, editorPath, parseMetalographyPath } from "./route";

const ID = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee";

describe("routes", () => {
  it("keeps list, create, editor and read-only view distinct", () => {
    expect(parseMetalographyPath("/apps/metalography").kind).toBe("list");
    expect(parseMetalographyPath(createPath()).kind).toBe("create");
    expect(parseMetalographyPath(editorPath(ID))).toEqual({ kind: "editor", reportId: ID, readOnly: false });
    expect(parseMetalographyPath(editorPath(ID, true))).toEqual({ kind: "editor", reportId: ID, readOnly: true });
  });

  it("does not treat an arbitrary suffix as a report", () => {
    expect(parseMetalographyPath("/apps/metalography/not-a-uuid").kind).toBe("list");
  });
});
