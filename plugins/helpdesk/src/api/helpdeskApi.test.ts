import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchTicketAttachmentBlob, listCategories } from "./helpdeskApi";

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function fakeResponse(body: string, status = 200): Response {
  return new Response(body, { status });
}

describe("fetchTicketAttachmentBlob", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("deduplica fetches concorrentes do mesmo documento", async () => {
    const gate = deferred<Response>();
    const fetchMock = vi.fn().mockReturnValue(gate.promise);
    vi.stubGlobal("fetch", fetchMock);

    const first = fetchTicketAttachmentBlob("1299", 1344);
    const second = fetchTicketAttachmentBlob("1299", 1344);
    gate.resolve(fakeResponse("PNGDATA"));

    const [a, b] = await Promise.all([first, second]);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(a).toBe(b);
  });

  it("documentos distintos não compartilham o mesmo request", async () => {
    const fetchMock = vi.fn(async () => fakeResponse("PNGDATA"));
    vi.stubGlobal("fetch", fetchMock);

    await Promise.all([
      fetchTicketAttachmentBlob("1299", 1344),
      fetchTicketAttachmentBlob("1299", 1345),
    ]);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("após concluir, um novo fetch é permitido", async () => {
    const fetchMock = vi.fn(async () => fakeResponse("PNGDATA"));
    vi.stubGlobal("fetch", fetchMock);

    await fetchTicketAttachmentBlob("1299", 1344);
    await fetchTicketAttachmentBlob("1299", 1344);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("erro não fica retido: retentativa posterior refaz o request", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(fakeResponse('{"error":"forbidden"}', 403))
      .mockResolvedValueOnce(fakeResponse("PNGDATA"));
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchTicketAttachmentBlob("1299", 1344)).rejects.toMatchObject({
      code: "forbidden",
      status: 403,
    });
    await expect(fetchTicketAttachmentBlob("1299", 1344)).resolves.toBeInstanceOf(Blob);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});

describe("listCategories", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("ordena categorias por nome em pt-BR com números naturais e mantém os IDs do GLPI", async () => {
    const items = [
      { id: 42, name: "TI 10" },
      { id: 7, name: "Zebra" },
      { id: 11, name: "Árvore" },
      { id: 38, name: "TI 2" },
      { id: 5, name: "análise" },
    ];
    const fetchMock = vi.fn(async () => fakeResponse(JSON.stringify({ items })));
    vi.stubGlobal("fetch", fetchMock);

    const response = await listCategories();

    expect(response.items).toEqual([
      { id: 5, name: "análise" },
      { id: 11, name: "Árvore" },
      { id: 38, name: "TI 2" },
      { id: 42, name: "TI 10" },
      { id: 7, name: "Zebra" },
    ]);
    expect(fetchMock).toHaveBeenCalledWith(
      "/apps/helpdesk-api/ticket-categories",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
    // O catálogo do GLPI permanece intacto; apenas a apresentação é ordenada.
    expect(items[0]).toEqual({ id: 42, name: "TI 10" });
  });

  it("mantém desempate determinístico pelo ID para nomes equivalentes", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => fakeResponse(JSON.stringify({
      items: [
        { id: 20, name: "ÁREA" },
        { id: 8, name: "area" },
        { id: 15, name: "Área" },
      ],
    }))));

    const response = await listCategories();

    expect(response.items.map((item) => item.id)).toEqual([8, 15, 20]);
  });
});
