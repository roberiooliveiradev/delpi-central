import { beforeEach, describe, expect, it, vi } from "vitest";

const httpGet = vi.fn();
const httpPost = vi.fn();

vi.mock("./httpClient", () => ({
  httpGet: (...args: unknown[]) => httpGet(...args),
  httpPost: (...args: unknown[]) => httpPost(...args),
}));

import { searchDirectoryUsers } from "./directoryApi";

describe("searchDirectoryUsers", () => {
  beforeEach(() => {
    httpGet.mockReset();
    httpGet.mockResolvedValue({ items: [] });
  });

  it("filtra por app tv-dashboard por padrão", async () => {
    await searchDirectoryUsers("ana", 8);
    expect(httpGet).toHaveBeenCalledTimes(1);
    const url = String(httpGet.mock.calls[0]?.[0] ?? "");
    expect(url).toContain("/core-api/me/directory/users?");
    expect(url).toContain("app=tv-dashboard");
    expect(url).toContain("q=ana");
  });

  it("inclui permission quando pedida (papel Editor)", async () => {
    await searchDirectoryUsers("ana", 8, undefined, {
      permission: "tv-dashboard.write",
    });
    const url = String(httpGet.mock.calls[0]?.[0] ?? "");
    expect(url).toContain("permission=tv-dashboard.write");
  });

  it("não busca com menos de 2 caracteres", async () => {
    await expect(searchDirectoryUsers("a")).resolves.toEqual([]);
    expect(httpGet).not.toHaveBeenCalled();
  });
});
