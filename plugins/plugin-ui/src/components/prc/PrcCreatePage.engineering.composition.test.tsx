/** GLPI #1621 / S1b — ENG-PRC-GLPI-1621-S1B-MY-REQUESTS-MP-PREFILL-01.
 *
 * Teste de INTEGRAÇÃO REAL do consumidor: monta `PrcCreatePage` de
 * `plugins/engineering` (não um mock de source) sobre o
 * `PrcRequestForm` compartilhado, com o adapter da Engineering API
 * mockado apenas na fronteira HTTP.
 *
 * Contratos verificados:
 * - AC-1621-S1B-02/10: Tipo inicia em «Selecionar…» enquanto Armazém
 *   `01` e Conta `11401002` seguem pré-selecionados (S1 preservado);
 * - AC-1621-S1B-03/10: escolha manual `PA` é livre e sobrevive a
 *   voltar/avançar;
 * - AC-1621-S1B-04/10: o envio real da página leva
 *   `requestedData.productKind` = escolha do usuário e
 *   `source="portal-engineering"` — nunca `MP` forçado.
 */

import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { PrcReferenceData } from "../../utils/prcProductRegistration";

/* vi.mock é içado: o specifier do módulo precisa ser literal. */

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

const prcIntakeSubmit = vi.fn();
vi.mock(
  "../../../../engineering/src/features/product-registration/api/productRegistrationApi",
  () => ({
    fetchPrcReferenceData: vi.fn().mockResolvedValue({ data: REF_DATA }),
  fetchPrcCatalog: vi.fn((kind: string) =>
    Promise.resolve({ data: { items: CATALOGS[kind] ?? [] } }),
  ),
  searchPrcSuppliers: vi
    .fn()
    .mockResolvedValue({ data: { items: [SUPPLIER_HIT] } }),
  fetchPrcEditContext: vi.fn(),
  prcIntakeSubmit: (...args: unknown[]) => prcIntakeSubmit(...args),
  uploadPrcAttachment: vi.fn().mockResolvedValue({}),
}));

/* Import tardio: o módulo da página é carregado já com a API mockada. */
const { PrcCreatePage } = await import(
  "../../../../engineering/src/features/product-registration/pages/PrcCreatePage"
);

afterEach(() => {
  cleanup();
  prcIntakeSubmit.mockReset();
});

function advance() {
  fireEvent.click(screen.getAllByRole("button", { name: "Avançar" })[0]);
}

async function goToSheet() {
  await waitFor(() => screen.getAllByText("O que precisa ser feito?"));
  advance();
  await waitFor(() =>
    expect(document.getElementById("prc-new-description")).toBeTruthy(),
  );
}

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

describe("PrcCreatePage real (Portal Engenharia) — S1b paridade", () => {
  it("Tipo inicia em Selecionar…, armazém/conta do S1 pré-selecionados, opções MP/PA/PI intactas", async () => {
    render(<PrcCreatePage basePath="/apps/engineering" />);
    await goToSheet();
    await waitFor(() =>
      expect(selectTrigger("productKind").disabled).toBe(false),
    );
    /* S1b: Tipo sem pré-seleção na jornada ampla de Engenharia. */
    expect(selectTrigger("productKind").textContent).toContain(
      "Selecionar…",
    );
    /* S1 preservado nos dois canais. */
    expect(selectTrigger("defaultWarehouse").textContent).toContain(
      "01",
    );
    expect(selectTrigger("accountingAccount").textContent).toContain(
      "11401002",
    );
    /* Catálogo oficial completo segue ofertado. */
    fireEvent.click(selectTrigger("productKind"));
    await screen.findByRole("button", { name: /MP — Matéria-prima/ });
    screen.getByRole("button", { name: /PA — Produto acabado/ });
    screen.getByRole("button", { name: /PI — Produto intermediário/ });
    },
    30000,
  );

  it("escolha manual PA sobrevive voltar/avançar e é enviada com source portal-engineering", async () => {
    prcIntakeSubmit.mockResolvedValue({ data: { requestId: "req-eng" } });
    render(<PrcCreatePage basePath="/apps/engineering" />);
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
    /* Completa a ficha real e envia. */
    fireEvent.change(
      document.getElementById("prc-new-description") as HTMLInputElement,
      { target: { value: "PRODUTO ACABADO ENG" } },
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
    await waitFor(() =>
      expect(prcIntakeSubmit).toHaveBeenCalledTimes(1),
    );
    const [body, idem] = prcIntakeSubmit.mock.calls[0];
    expect(idem).toMatch(/^prc-intake-/);
    expect(body.requestType).toBe("create");
    /* source real da página — prova de que não é um mock de canal. */
    expect(body.source).toBe("portal-engineering");
    expect(body.requestedData.productKind).toBe("PA");
    expect(body.requestedData.defaultWarehouse).toBe("01");
    expect(body.requestedData.accountingAccount).toBe("11401002");
    },
    30000,
  );
});
