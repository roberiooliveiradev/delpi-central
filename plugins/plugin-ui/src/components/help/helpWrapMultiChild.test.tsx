import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HelpTooltip } from "./HelpTooltip";

afterEach(cleanup);

function keyWarns(spy: ReturnType<typeof vi.spyOn>) {
  return spy.mock.calls.filter(
    (c) => String(c[0] ?? "").includes("unique") && String(c[0] ?? "").includes("key"),
  );
}

describe("HelpTooltip wrap keys", () => {
  it("array explícito de filhos sem key não gera warning", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <HelpTooltip content="ajuda" wrap>
        {[<span>a</span>, <span>b</span>]}
      </HelpTooltip>,
    );
    expect(keyWarns(spy)).toEqual([]);
    spy.mockRestore();
  });

  it("filho único continua ok", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <HelpTooltip content="ajuda" wrap>
        <span>rótulo</span>
      </HelpTooltip>,
    );
    expect(keyWarns(spy)).toEqual([]);
    spy.mockRestore();
  });
});
