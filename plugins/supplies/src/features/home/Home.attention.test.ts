import { beforeEach, describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  getHomeAttentionSnapshot,
  loadHomeAttention,
  resetHomeAttentionStoreForTests,
  subscribeHomeAttention,
} from "../../app/homeAttentionStore";

const dir = dirname(fileURLToPath(import.meta.url));

vi.mock("../../api/homeAttention", () => ({
  getHomeAttention: vi.fn(),
}));

import { getHomeAttention } from "../../api/homeAttention";

const mockedGet = vi.mocked(getHomeAttention);

describe("Home attention UX", () => {
  beforeEach(() => {
    resetHomeAttentionStoreForTests();
    mockedGet.mockReset();
  });

  it("página usa LoadingCard, erro com retry e store compartilhada", () => {
    const page = readFileSync(join(dir, "../../pages/HomePage.tsx"), "utf8");
    const shell = readFileSync(join(dir, "../../app/PluginShell.tsx"), "utf8");
    expect(page).toMatch(/SuppliesLoadingCard/);
    expect(page).toMatch(/HOME\.attentionError/);
    expect(page).toMatch(/attentionRefresh/);
    expect(page).toMatch(/attentionPartial/);
    expect(page).toMatch(/loadHomeAttention/);
    expect(page).toMatch(/subscribeHomeAttention/);
    expect(shell).toMatch(/subscribeHomeAttention/);
    expect(shell).toMatch(/loadHomeAttention/);
  });

  it("positive: carrega cards e limpa erro", async () => {
    mockedGet.mockResolvedValueOnce({
      cards: [
        {
          id: "pr",
          viewId: "purchase_requests",
          title: "SC",
          description: "desc",
          requiredCap: "purchaseRequests",
          count: null,
          status: "available",
        },
      ],
      partialFailures: [],
    });
    const snapshots: string[] = [];
    const unsubscribe = subscribeHomeAttention((state) => {
      snapshots.push(state.loading ? "loading" : state.error ? "error" : "ok");
    });
    await loadHomeAttention();
    unsubscribe();
    expect(getHomeAttentionSnapshot().cards).toHaveLength(1);
    expect(getHomeAttentionSnapshot().error).toBeNull();
    expect(snapshots).toContain("loading");
    expect(snapshots.at(-1)).toBe("ok");
  });

  it("negative: falha mantém caminhos utilizáveis (erro amigável no store)", async () => {
    mockedGet.mockRejectedValueOnce(new Error("network down"));
    await loadHomeAttention();
    expect(getHomeAttentionSnapshot().cards).toEqual([]);
    expect(getHomeAttentionSnapshot().error).toMatch(/network down/);
    expect(getHomeAttentionSnapshot().loading).toBe(false);
  });

  it("sibling: partialFailures preservados sem derrubar cards", async () => {
    mockedGet.mockResolvedValueOnce({
      cards: [
        {
          id: "overview",
          viewId: "overview",
          title: "Visão geral",
          description: "desc",
          requiredCap: "analytics",
          count: null,
          status: "available",
        },
      ],
      partialFailures: [{ source: "aux", message: "fonte auxiliar falhou" }],
    });
    await loadHomeAttention();
    expect(getHomeAttentionSnapshot().cards).toHaveLength(1);
    expect(getHomeAttentionSnapshot().partialFailures).toHaveLength(1);
    expect(getHomeAttentionSnapshot().error).toBeNull();
  });
});
