/** GLPI #1621 / S1 — ENG-PRC-GLPI-1621-S1-FRONTEND-DEFAULTS-01.
 *
 * Valores iniciais aprovados pelo PO somente para NOVO CREATE de
 * matéria-prima (sem `editCase`): `defaultWarehouse="01"` e
 * `accountingAccount="11401002"`, sugestões editáveis da UI — nunca
 * regra autorizativa nem prova de cadastro ERP.
 *
 * Contratos verificados aqui:
 * - AC-01: os dois portais (source portal-engineering e my-requests)
 *   exibem os defaults na ficha técnica do CREATE novo;
 * - AC-02: o payload CREATE preserva os dois valores e a source real;
 * - AC-03: edição/limpeza manual é preservada; obrigatório zerado
 *   bloqueia sem repor o default;
 * - AC-04: UPDATE nunca apresenta nem envia defaults de CREATE, mesmo
 *   com consulta oficial lenta; string oficial vazia é preservada;
 * - AC-05: `editCase` semeia o draft (inclusive vazio), sem defaults;
 * - AC-06: fetch tardio de catálogo e alternância CREATE/UPDATE não
 *   sobrescrevem entrada manual nem injetam defaults em UPDATE. */

import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PrcRequestForm } from "./PrcRequestForm";
import type { PrcReferenceData } from "../../utils/prcProductRegistration";

const REF_DATA: PrcReferenceData = {
  schemaVersion: 1,
  productTypes: ["raw_material"],
  requestTypes: ["create", "update"],
  statuses: ["submitted"],
  sources: ["portal-engineering", "my-requests"],
  editableDraftPaths: [
    "description",
    "group",
    "productKind",
    "unit",
    "defaultWarehouse",
    "thirdPartyProduct",
    "accountingAccount",
    "customerReference",
    "suppliers",
  ],
  supplierKeys: { required: ["supplierCode"], optional: [] },
  fields: [
    {
      path: "description",
      kind: "text",
      requiredCreateIntake: true,
      verifiable: true,
      maxLength: 200,
    },
    {
      path: "group",
      kind: "code",
      requiredCreateIntake: true,
      verifiable: true,
      maxLength: 20,
    },
    {
      path: "productKind",
      kind: "code",
      requiredCreateIntake: true,
      verifiable: true,
      enumValues: ["MP", "PA", "PI"],
      maxLength: 8,
    },
    {
      path: "defaultWarehouse",
      kind: "code",
      requiredCreateIntake: true,
      verifiable: true,
      maxLength: 8,
    },
    {
      path: "unit",
      kind: "code",
      requiredCreateIntake: true,
      verifiable: true,
      maxLength: 8,
    },
    {
      path: "thirdPartyProduct",
      kind: "enum",
      requiredCreateIntake: true,
      verifiable: true,
      enumValues: ["1", "2"],
      maxLength: 2,
    },
    {
      path: "accountingAccount",
      kind: "code",
      requiredCreateIntake: true,
      verifiable: true,
      maxLength: 40,
    },
    {
      path: "customerReference",
      kind: "text",
      requiredCreateIntake: false,
      allowBlank: true,
      verifiable: true,
      maxLength: 60,
    },
    {
      path: "suppliers",
      kind: "suppliers",
      requiredCreateIntake: false,
      verifiable: true,
      maxLength: 0,
    },
  ],
};

const CATALOGS: Record<string, { code: string; label?: string }[]> = {
  "product-groups": [{ code: "100", label: "Matérias-primas" }],
  units: [
    { code: "KG", label: "Quilograma" },
    { code: "UN", label: "Unidade" },
  ],
  warehouses: [
    { code: "01", label: "Almox MP" },
    { code: "02", label: "Almox PA" },
  ],
  "accounting-accounts": [
    { code: "11401002", label: "Estoque MP" },
    { code: "11402001", label: "Estoque PA" },
  ],
};

const SUPPLIER_HIT = {
  supplier_code: "000123",
  supplier_store: "01",
  supplier_name: "WEG AMAZONIA SA",
  supplier_short_name: "WEG",
};

function provider(overrides: Record<string, unknown> = {}) {
  return {
    fetchReferenceData: vi.fn().mockResolvedValue(REF_DATA),
    fetchCatalog: vi.fn((kind: string) =>
      Promise.resolve({ data: { items: CATALOGS[kind] ?? [] } }),
    ),
    searchSuppliers: vi.fn().mockResolvedValue([SUPPLIER_HIT]),
    fetchEditContext: vi.fn(),
    submitIntake: vi.fn().mockResolvedValue({ requestId: "req-new" }),
    uploadAttachment: vi.fn().mockResolvedValue({}),
    saveDraft: vi.fn().mockResolvedValue({}),
    ...overrides,
  };
}

afterEach(cleanup);

function renderForm(
  dp: ReturnType<typeof provider>,
  source: string,
  extra: Record<string, unknown> = {},
) {
  return render(
    <PrcRequestForm
      source={source}
      dataProvider={dp as never}
      onCancel={() => undefined}
      onCompleted={() => undefined}
      {...extra}
    />,
  );
}

function advance() {
  fireEvent.click(
    screen.getAllByRole("button", { name: "Avançar" })[0],
  );
}

async function goToSheet() {
  await waitFor(() => screen.getAllByText("O que precisa ser feito?"));
  advance();
  await waitFor(() =>
    expect(document.getElementById("prc-new-description")).toBeTruthy(),
  );
}

/** Trigger do select compartilhado (`<button id="prc-new-<path>">`). */
function selectTrigger(path: string): HTMLButtonElement {
  const el = document.getElementById(`prc-new-${path}`);
  expect(el, `trigger ${path}`).toBeTruthy();
  return el as HTMLButtonElement;
}

async function pickOption(triggerId: string, name: string | RegExp) {
  fireEvent.click(document.getElementById(triggerId)!);
  fireEvent.click(
    await screen.findByRole("button", { name }, { timeout: 3000 }),
  );
}

describe("PrcRequestForm — GLPI #1621 S1 defaults CREATE", () => {
  it.each(["portal-engineering", "my-requests"] as const)(
    "AC-01: novo CREATE em %s exibe Armazém 01 e Conta 11401002 editáveis",
    async (source) => {
      const dp = provider();
      renderForm(dp, source);
      await goToSheet();
      await waitFor(() =>
        expect(selectTrigger("defaultWarehouse").disabled).toBe(false),
      );
      expect(selectTrigger("defaultWarehouse").textContent).toContain(
        "01",
      );
      expect(
        selectTrigger("accountingAccount").textContent,
      ).toContain("11401002");
      expect(selectTrigger("accountingAccount").disabled).toBe(false);
    },
  );

  it("AC-02: submissão CREATE preserva requestedData com os defaults e a source real", async () => {
    const dp = provider();
    renderForm(dp, "portal-engineering");
    await goToSheet();
    fireEvent.change(
      document.getElementById("prc-new-description") as HTMLInputElement,
      { target: { value: "RESINA EPOXI X" } },
    );
    await pickOption("prc-new-group", /100 — Matérias-primas/);
    await pickOption("prc-new-productKind", /MP — Matéria-prima/);
    await pickOption("prc-new-unit", /KG — Quilograma/);
    await pickOption("prc-new-thirdPartyProduct", /1 — Não/);
    /* defaults de armazém/conta permanecem sem toque manual. */
    fireEvent.click(
      screen.getAllByRole("button", {
        name: /Adicionar fornecedor/,
      })[0],
    );
    const searchBtn = await screen.findByRole("button", {
      name: /Buscar fornecedor da linha 1/,
    });
    fireEvent.click(searchBtn);
    const lookup = await screen.findByRole("textbox", {
      name: /Buscar fornecedor/,
    });
    fireEvent.change(lookup, { target: { value: "weg" } });
    fireEvent.click(
      await screen.findByRole("button", { name: /WEG AMAZONIA SA/ }),
    );
    fireEvent.change(
      await screen.findByRole("textbox", { name: "Part Number" }),
      { target: { value: "PN-1" } },
    );
    advance();
    await waitFor(() => screen.getAllByText("Resumo da solicitação"));
    fireEvent.click(
      screen.getAllByRole("button", { name: "Enviar solicitação" })[0],
    );
    await waitFor(() =>
      expect(dp.submitIntake).toHaveBeenCalledTimes(1),
    );
    const [body, idem] = dp.submitIntake.mock.calls[0];
    expect(idem).toMatch(/^prc-intake-/);
    expect(body.requestType).toBe("create");
    expect(body.source).toBe("portal-engineering");
    expect(body.requestedData.defaultWarehouse).toBe("01");
    expect(body.requestedData.accountingAccount).toBe("11401002");
    expect(body.requestedData.description).toBe("RESINA EPOXI X");
    expect(dp.saveDraft).not.toHaveBeenCalled();
  });

  it("AC-03: edição manual sobrevive a voltar/avançar; limpeza bloqueia sem repor default", async () => {
    const dp = provider();
    renderForm(dp, "my-requests");
    await goToSheet();
    await pickOption("prc-new-defaultWarehouse", /02 — Almox PA/);
    await pickOption(
      "prc-new-accountingAccount",
      /11402001 — Estoque PA/,
    );
    /* Volta à identificação e retorna — entrada manual preservada. */
    fireEvent.click(screen.getAllByRole("button", { name: "Voltar" })[0]);
    await waitFor(() => screen.getAllByText("O que precisa ser feito?"));
    advance();
    await waitFor(() =>
      expect(selectTrigger("defaultWarehouse").textContent).toContain(
        "02",
      ),
    );
    expect(selectTrigger("accountingAccount").textContent).toContain(
      "11402001",
    );
    /* Zerar um obrigatório bloqueia o avanço — e nada repõe default
     * nem perde as escolhas já feitas nos campos com sugestão. */
    const desc = document.getElementById(
      "prc-new-description",
    ) as HTMLInputElement;
    fireEvent.change(desc, { target: { value: "RESINA Y" } });
    fireEvent.change(desc, { target: { value: "" } });
    advance();
    await waitFor(() =>
      expect(screen.getByText(/Preencha «Descrição»/)).toBeTruthy(),
    );
    expect(selectTrigger("defaultWarehouse").textContent).toContain(
      "02",
    );
    expect(selectTrigger("accountingAccount").textContent).toContain(
      "11402001",
    );
    expect(
      selectTrigger("accountingAccount").textContent,
    ).not.toContain("11401002");
    expect(dp.submitIntake).not.toHaveBeenCalled();
  });

  it("AC-04: UPDATE não apresenta nem envia defaults, mesmo com consulta lenta; vazio oficial é preservado", async () => {
    let resolveCtx!: (v: unknown) => void;
    const dp = provider({
      fetchEditContext: vi.fn(
        () =>
          new Promise((r) => {
            resolveCtx = r;
          }),
      ),
    });
    renderForm(dp, "portal-engineering");
    await waitFor(() => screen.getAllByText("O que precisa ser feito?"));
    fireEvent.click(
      screen.getByRole("button", { name: "Alterar produto existente" }),
    );
    fireEvent.change(
      document.getElementById("prc-new-official-code") as HTMLInputElement,
      { target: { value: "001234" } },
    );
    advance();
    /* Consulta oficial pendente: defaults de CREATE não aparecem na
     * ficha UPDATE nem como sugestão nem como alteração. */
    await waitFor(() =>
      expect(
        document.getElementById("prc-new-defaultWarehouse"),
      ).toBeTruthy(),
    );
    expect(
      selectTrigger("defaultWarehouse").textContent,
    ).not.toContain("01 — Almox MP");
    expect(
      selectTrigger("accountingAccount").textContent,
    ).not.toContain("11401002");
    resolveCtx({
      status: "available",
      officialCode: "001234",
      fingerprint: "fp-1",
      readAt: "2026-11-19T10:00:00Z",
      fields: {
        description: { value: "RESINA OFICIAL" },
        group: { value: "100" },
        productKind: { value: "MP" },
        unit: { value: "KG" },
        defaultWarehouse: { value: "05" },
        thirdPartyProduct: { value: "1" },
        accountingAccount: { value: "" },
        customerReference: { value: "" },
      },
      links: [],
      linksComplete: true,
    });
    await waitFor(() =>
      expect(selectTrigger("defaultWarehouse").textContent).toContain(
        "05",
      ),
    );
    expect(
      selectTrigger("accountingAccount").textContent,
    ).not.toContain("11401002");
    /* Uma única alteração real → changes só trazem esse campo. */
    fireEvent.change(
      document.getElementById("prc-new-description") as HTMLInputElement,
      { target: { value: "RESINA OFICIAL V2" } },
    );
    advance();
    await waitFor(() => screen.getAllByText("Resumo da solicitação"));
    fireEvent.click(
      screen.getAllByRole("button", { name: "Enviar solicitação" })[0],
    );
    await waitFor(() =>
      expect(dp.submitIntake).toHaveBeenCalledTimes(1),
    );
    const [body] = dp.submitIntake.mock.calls[0];
    expect(body.requestType).toBe("update");
    expect(body.officialProductCode).toBe("001234");
    const changedPaths = body.changes.map(
      (c: { path: string }) => c.path,
    );
    expect(changedPaths).toEqual(["description"]);
    expect(changedPaths).not.toContain("defaultWarehouse");
    expect(changedPaths).not.toContain("accountingAccount");
  });

  it("AC-05: editCase CREATE semeia o draft (inclusive vazio), sem defaults de CREATE novo", async () => {
    const dp = provider();
    render(
      <PrcRequestForm
        source="my-requests"
        dataProvider={dp as never}
        onCancel={() => undefined}
        onCompleted={() => undefined}
        editCase={{
          requestId: "req-9",
          expectedVersion: 4,
          requestType: "create",
          draft: {
            description: "RESINA DRAFT",
            unit: "KG",
            defaultWarehouse: "03",
            suppliers: [
              {
                supplierCode: "000001",
                store: "01",
                supplierName: "FORN X",
                partNumber: "PN-1",
              },
            ],
          },
        }}
      />,
    );
    await waitFor(() => screen.getAllByDisplayValue("RESINA DRAFT"));
    /* draft.defaultWarehouse=03 preservado; accountingAccount ausente
     * no draft NÃO recebe o default de CREATE novo. */
    expect(selectTrigger("defaultWarehouse").textContent).toContain(
      "03",
    );
    expect(
      selectTrigger("accountingAccount").textContent,
    ).not.toContain("11401002");
  });

  it("AC-06: catálogo tardio não sobrescreve edição manual; alternar UPDATE→CREATE não injeta em UPDATE", async () => {
    let resolveAccounts!: (v: unknown) => void;
    const dp = provider({
      fetchCatalog: vi.fn((kind: string) => {
        if (kind === "accounting-accounts") {
          return new Promise((r) => {
            resolveAccounts = r;
          });
        }
        return Promise.resolve({ data: { items: CATALOGS[kind] ?? [] } });
      }),
    });
    renderForm(dp, "my-requests");
    await goToSheet();
    await pickOption("prc-new-defaultWarehouse", /02 — Almox PA/);
    /* Catálogo de contas resolve tarde — não sobrescreve o armazém
     * editado nem o próprio default de conta. */
    resolveAccounts({
      data: { items: CATALOGS["accounting-accounts"] },
    });
    await waitFor(() =>
      expect(selectTrigger("accountingAccount").disabled).toBe(false),
    );
    expect(selectTrigger("defaultWarehouse").textContent).toContain(
      "02",
    );
    expect(
      selectTrigger("accountingAccount").textContent,
    ).toContain("11401002");
    /* UPDATE: sugestão intacta não migra; volta ao CREATE repõe só
     * onde não há entrada manual. */
    fireEvent.click(screen.getAllByRole("button", { name: "Voltar" })[0]);
    await waitFor(() => screen.getAllByText("O que precisa ser feito?"));
    fireEvent.click(
      screen.getByRole("button", { name: "Alterar produto existente" }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Criar cadastro de matéria-prima" }),
    );
    advance();
    await waitFor(() =>
      expect(document.getElementById("prc-new-defaultWarehouse")).toBeTruthy(),
    );
    expect(selectTrigger("defaultWarehouse").textContent).toContain(
      "02",
    );
    expect(
      selectTrigger("accountingAccount").textContent,
    ).toContain("11401002");
  });
});

describe("PrcRequestForm — GLPI #1621 S1b Tipo MP só no My Requests", () => {
  /* Monta o fluxo CREATE completo e envia; retorna o body capturado. */
  async function submitCreate(dp: ReturnType<typeof provider>) {
    fireEvent.change(
      document.getElementById("prc-new-description") as HTMLInputElement,
      { target: { value: "RESINA S1B" } },
    );
    await pickOption("prc-new-group", /100 — Matérias-primas/);
    await pickOption("prc-new-unit", /KG — Quilograma/);
    await pickOption("prc-new-thirdPartyProduct", /1 — Não/);
    fireEvent.click(
      screen.getAllByRole("button", { name: /Adicionar fornecedor/ })[0],
    );
    fireEvent.click(
      await screen.findByRole("button", {
        name: /Buscar fornecedor da linha 1/,
      }),
    );
    fireEvent.change(
      await screen.findByRole("textbox", { name: /Buscar fornecedor/ }),
      { target: { value: "weg" } },
    );
    fireEvent.click(
      await screen.findByRole("button", { name: /WEG AMAZONIA SA/ }),
    );
    fireEvent.change(
      await screen.findByRole("textbox", { name: "Part Number" }),
      { target: { value: "PN-1" } },
    );
    advance();
    await waitFor(() => screen.getAllByText("Resumo da solicitação"));
    fireEvent.click(
      screen.getAllByRole("button", { name: "Enviar solicitação" })[0],
    );
    await waitFor(() => expect(dp.submitIntake).toHaveBeenCalledTimes(1));
    return dp.submitIntake.mock.calls[0][0];
  }

  it("S1B-01: my-requests exibe Tipo MP + Armazém 01 + Conta 11401002 no novo CREATE", async () => {
    renderForm(provider(), "my-requests");
    await goToSheet();
    await waitFor(() =>
      expect(selectTrigger("productKind").disabled).toBe(false),
    );
    expect(selectTrigger("productKind").textContent).toContain(
      "MP — Matéria-prima",
    );
    expect(selectTrigger("defaultWarehouse").textContent).toContain("01");
    expect(selectTrigger("accountingAccount").textContent).toContain(
      "11401002",
    );
  });

  it("S1B-02: portal-engineering mantém Tipo em Selecionar… e opções oficiais MP/PA/PI", async () => {
    renderForm(provider(), "portal-engineering");
    await goToSheet();
    await waitFor(() =>
      expect(selectTrigger("productKind").disabled).toBe(false),
    );
    expect(selectTrigger("productKind").textContent).toContain(
      "Selecionar…",
    );
    expect(selectTrigger("defaultWarehouse").textContent).toContain("01");
    expect(selectTrigger("accountingAccount").textContent).toContain(
      "11401002",
    );
    fireEvent.click(selectTrigger("productKind"));
    await screen.findByRole("button", { name: /MP — Matéria-prima/ });
    screen.getByRole("button", { name: /PA — Produto acabado/ });
    screen.getByRole("button", { name: /PI — Produto intermediário/ });
  });

  it("S1B-03: my-requests troca MP por PA; voltar/avançar e envio preservam PA", async () => {
    const dp = provider();
    renderForm(dp, "my-requests");
    await goToSheet();
    await pickOption("prc-new-productKind", /PA — Produto acabado/);
    fireEvent.click(
      screen.getAllByRole("button", { name: "Voltar" })[0],
    );
    await waitFor(() => screen.getAllByText("O que precisa ser feito?"));
    advance();
    await waitFor(() =>
      expect(selectTrigger("productKind").textContent).toContain(
        "PA — Produto acabado",
      ),
    );
    const body = await submitCreate(dp);
    expect(body.requestType).toBe("create");
    expect(body.source).toBe("my-requests");
    expect(body.requestedData.productKind).toBe("PA");
    expect(body.requestedData.defaultWarehouse).toBe("01");
    expect(body.requestedData.accountingAccount).toBe("11401002");
  });

  it("S1B-04: CREATE my-requests intacto envia productKind=MP e source=my-requests", async () => {
    const dp = provider();
    renderForm(dp, "my-requests");
    await goToSheet();
    /* Tipo e demais sugestões sem toque manual. */
    const body = await submitCreate(dp);
    expect(body.source).toBe("my-requests");
    expect(body.requestedData.productKind).toBe("MP");
  });

  it("S1B-05: UPDATE my-requests com oficial PA não mostra MP; changes só trazem alterado", async () => {
    let resolveCtx!: (v: unknown) => void;
    const dp = provider({
      fetchEditContext: vi.fn(
        () =>
          new Promise((r) => {
            resolveCtx = r;
          }),
      ),
    });
    renderForm(dp, "my-requests");
    await waitFor(() => screen.getAllByText("O que precisa ser feito?"));
    fireEvent.click(
      screen.getByRole("button", { name: "Alterar produto existente" }),
    );
    fireEvent.change(
      document.getElementById(
        "prc-new-official-code",
      ) as HTMLInputElement,
      { target: { value: "007777" } },
    );
    advance();
    await waitFor(() =>
      expect(document.getElementById("prc-new-productKind")).toBeTruthy(),
    );
    /* Consulta lenta: sugestões de CREATE (inclusive MP) não aparecem. */
    expect(selectTrigger("productKind").textContent).not.toContain(
      "Matéria-prima",
    );
    resolveCtx({
      status: "available",
      officialCode: "007777",
      fingerprint: "fp-2",
      readAt: "2026-11-19T12:00:00Z",
      fields: {
        description: { value: "PROD OFICIAL PA" },
        group: { value: "100" },
        productKind: { value: "PA" },
        unit: { value: "KG" },
        defaultWarehouse: { value: "02" },
        thirdPartyProduct: { value: "1" },
        accountingAccount: { value: "" },
        customerReference: { value: "" },
      },
      links: [],
      linksComplete: true,
    });
    await waitFor(() =>
      expect(selectTrigger("productKind").textContent).toContain(
        "PA — Produto acabado",
      ),
    );
    expect(selectTrigger("defaultWarehouse").textContent).toContain("02");
    fireEvent.change(
      document.getElementById("prc-new-description") as HTMLInputElement,
      { target: { value: "PROD OFICIAL PA V2" } },
    );
    advance();
    await waitFor(() => screen.getAllByText("Resumo da solicitação"));
    fireEvent.click(
      screen.getAllByRole("button", { name: "Enviar solicitação" })[0],
    );
    await waitFor(() => expect(dp.submitIntake).toHaveBeenCalledTimes(1));
    const [body] = dp.submitIntake.mock.calls[0];
    const changedPaths = body.changes.map(
      (c: { path: string }) => c.path,
    );
    expect(changedPaths).toEqual(["description"]);
    expect(changedPaths).not.toContain("productKind");
    expect(changedPaths).not.toContain("defaultWarehouse");
    expect(changedPaths).not.toContain("accountingAccount");
  });

  it("S1B-06: editCase semeia draft.productKind; ausente/vazio não recebe MP", async () => {
    const dp = provider();
    const { unmount } = render(
      <PrcRequestForm
        source="my-requests"
        dataProvider={dp as never}
        onCancel={() => undefined}
        onCompleted={() => undefined}
        editCase={{
          requestId: "req-20",
          expectedVersion: 2,
          requestType: "create",
          draft: {
            description: "DRAFT PA",
            productKind: "PA",
            unit: "KG",
            suppliers: [
              {
                supplierCode: "000001",
                store: "01",
                supplierName: "FORN X",
                partNumber: "PN-1",
              },
            ],
          },
        }}
      />,
    );
    await waitFor(() => screen.getAllByDisplayValue("DRAFT PA"));
    expect(selectTrigger("productKind").textContent).toContain(
      "PA — Produto acabado",
    );
    unmount();
    render(
      <PrcRequestForm
        source="my-requests"
        dataProvider={dp as never}
        onCancel={() => undefined}
        onCompleted={() => undefined}
        editCase={{
          requestId: "req-21",
          expectedVersion: 1,
          requestType: "create",
          draft: {
            description: "DRAFT SEM TIPO",
            unit: "KG",
            suppliers: [],
          },
        }}
      />,
    );
    await waitFor(() => screen.getAllByDisplayValue("DRAFT SEM TIPO"));
    expect(selectTrigger("productKind").textContent).not.toContain(
      "Matéria-prima",
    );
  });

  it("S1B-07: UPDATE→CREATE repõe MP só onde vazio; seleção manual PA sobrevive ao ciclo", async () => {
    const dp = provider();
    renderForm(dp, "my-requests");
    await goToSheet();
    await pickOption("prc-new-productKind", /PA — Produto acabado/);
    fireEvent.click(
      screen.getAllByRole("button", { name: "Voltar" })[0],
    );
    await waitFor(() => screen.getAllByText("O que precisa ser feito?"));
    /* Ida ao UPDATE retira sugestões intactas mas preserva PA manual. */
    fireEvent.click(
      screen.getByRole("button", { name: "Alterar produto existente" }),
    );
    fireEvent.click(
      screen.getByRole("button", {
        name: "Criar cadastro de matéria-prima",
      }),
    );
    advance();
    await waitFor(() =>
      expect(document.getElementById("prc-new-productKind")).toBeTruthy(),
    );
    expect(selectTrigger("productKind").textContent).toContain(
      "PA — Produto acabado",
    );
    expect(selectTrigger("defaultWarehouse").textContent).toContain("01");
    expect(selectTrigger("accountingAccount").textContent).toContain(
      "11401002",
    );
  });
});
