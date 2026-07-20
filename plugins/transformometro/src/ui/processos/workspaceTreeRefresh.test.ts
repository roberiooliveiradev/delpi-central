import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import {
  TRANSFORMOMETRO_WORKSPACE_TREE_REFRESH_EVENT,
  requestWorkspaceTreeRefresh,
} from "../../utils/navigation";

describe("requestWorkspaceTreeRefresh", () => {
  beforeEach(() => {
    vi.stubGlobal("window", {
      dispatchEvent: vi.fn(),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("dispara evento para recarregar a árvore do workspace", () => {
    requestWorkspaceTreeRefresh();
    expect(window.dispatchEvent).toHaveBeenCalledWith(
      expect.objectContaining({ type: TRANSFORMOMETRO_WORKSPACE_TREE_REFRESH_EVENT })
    );
  });
});
