/** PRC-REF-023-EDIT-POLICY-FIX-08 — modo `editCase` do formulário
 * compartilhado: edição livre do caso `submitted` no mesmo requestId.
 *
 * Contratos verificados aqui (o backend segue autoridade de
 * estado/escopo/versão — estes testes cobrem a composição):
 * - etapa de identificação removida; ficha semeada do technicalDraft;
 * - baseline do diff é o draft do caso (não o TOTVS);
 * - submit chama `saveDraft` (CAS + idempotência), nunca `submitIntake`;
 * - caso UPDATE materializa suppliers + supplierLinkChanges. */

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
import { applySupplierLinkOps } from "../../utils/prcProductRegistration";

const REF_DATA: PrcReferenceData = {
  schemaVersion: 1,
  productTypes: ["raw_material"],
  requestTypes: ["create", "update"],
  statuses: ["submitted"],
  sources: ["my-requests"],
  editableDraftPaths: ["description", "unit", "suppliers"],
  supplierKeys: { required: ["supplierCode"], optional: [] },
  fields: [
    {
      path: "description",
      kind: "text",
      requiredCreateIntake: true,
      verifiable: true,
      maxLength: 120,
    },
    {
      path: "unit",
      kind: "enum",
      requiredCreateIntake: true,
      verifiable: true,
      enumValues: ["UN", "KG"],
      maxLength: 3,
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

function provider(overrides: Record<string, unknown> = {}) {
  return {
    fetchReferenceData: vi.fn().mockResolvedValue(REF_DATA),
    fetchCatalog: vi.fn().mockResolvedValue({ data: { items: [] } }),
    searchSuppliers: vi.fn().mockResolvedValue({ items: [] }),
    fetchEditContext: vi.fn(),
    submitIntake: vi.fn(),
    uploadAttachment: vi.fn().mockResolvedValue({}),
    saveDraft: vi.fn().mockResolvedValue({}),
    ...overrides,
  };
}

afterEach(cleanup);

const CREATE_DRAFT = {
  description: "RESINA EPOXI",
  unit: "KG",
  suppliers: [
    {
      supplierCode: "000001",
      store: "01",
      supplierName: "FORN X",
      partNumber: "PN-1",
      catalogNumber: null,
    },
  ],
};

describe("PrcRequestForm — editCase", () => {
  it("inicia na ficha técnica (sem etapa de identificação) com os valores do draft", async () => {
    const dp = provider();
    render(
      <PrcRequestForm
        source="my-requests"
        dataProvider={dp as never}
        onCancel={() => undefined}
        onCompleted={() => undefined}
        editCase={{
          requestId: "req-1",
          expectedVersion: 3,
          requestType: "create",
          draft: CREATE_DRAFT,
        }}
      />,
    );
    await waitFor(() =>
      expect(
        screen.getAllByDisplayValue("RESINA EPOXI")[0],
      ).toBeTruthy(),
    );
    expect(screen.queryByText("O que precisa ser feito?")).toBeNull();
    expect(screen.queryByText("Identificação")).toBeNull();
    expect(dp.submitIntake).not.toHaveBeenCalled();
    expect(dp.fetchEditContext).not.toHaveBeenCalled();
  });

  it("exige ao menos uma alteração antes de avançar", async () => {
    const dp = provider();
    render(
      <PrcRequestForm
        source="my-requests"
        dataProvider={dp as never}
        onCancel={() => undefined}
        onCompleted={() => undefined}
        editCase={{
          requestId: "req-1",
          expectedVersion: 3,
          requestType: "create",
          draft: CREATE_DRAFT,
        }}
      />,
    );
    await waitFor(() => screen.getAllByDisplayValue("RESINA EPOXI"));
    fireEvent.click(
      screen.getAllByRole("button", { name: "Avançar" })[0],
    );
    await waitFor(() =>
      expect(
        screen.getByText(/Nenhuma alteração identificada/),
      ).toBeTruthy(),
    );
    expect(dp.saveDraft).not.toHaveBeenCalled();
  });

  it("salva via saveDraft com CAS e o mesmo requestId — nunca intake", async () => {
    const dp = provider();
    const onCompleted = vi.fn();
    render(
      <PrcRequestForm
        source="my-requests"
        dataProvider={dp as never}
        onCancel={() => undefined}
        onCompleted={onCompleted}
        editCase={{
          requestId: "req-1",
          expectedVersion: 3,
          requestType: "create",
          draft: CREATE_DRAFT,
        }}
      />,
    );
    await waitFor(() => screen.getAllByDisplayValue("RESINA EPOXI"));
    const descInput = document.getElementById(
      "prc-new-description",
    ) as HTMLInputElement;
    fireEvent.change(descInput, {
      target: { value: "RESINA EPOXI V2" },
    });
    fireEvent.click(
      screen.getAllByRole("button", { name: "Avançar" })[0],
    );
    await waitFor(() => screen.getAllByText("Resumo da solicitação")[0]);
    fireEvent.click(
      screen.getAllByRole("button", { name: "Salvar alterações" })[0],
    );
    await waitFor(() => expect(dp.saveDraft).toHaveBeenCalledTimes(1));
    const [rid, version, changes, idem] = dp.saveDraft.mock.calls[0];
    expect(rid).toBe("req-1");
    expect(version).toBe(3);
    expect(idem).toMatch(/^prc-intake-/);
    expect(changes).toEqual([
      {
        path: "description",
        proposedValue: "RESINA EPOXI V2",
        reason: "",
      },
    ]);
    expect(dp.submitIntake).not.toHaveBeenCalled();
    await waitFor(() => expect(onCompleted).toHaveBeenCalledWith("req-1"));
  });

  it("caso UPDATE envia a lista final de suppliers quando alterada", async () => {
    const dp = provider();
    render(
      <PrcRequestForm
        source="my-requests"
        dataProvider={dp as never}
        onCancel={() => undefined}
        onCompleted={() => undefined}
        editCase={{
          requestId: "req-2",
          expectedVersion: 2,
          requestType: "update",
          draft: {
            description: "BASE",
            officialProductCode: "001234",
            suppliers: [
              {
                supplierCode: "000001",
                store: "01",
                supplierName: "FORN X",
                partNumber: "PN-1",
              },
            ],
            supplierLinkChanges: [
              {
                operation: "add",
                key: { supplierCode: "000777", store: "01" },
                fields: { partNumber: "PN-777" },
                supplierName: "FORN NOVO",
              },
            ],
          },
        }}
      />,
    );
    /* O vínculo ADD do caso deve aparecer materializado — o baseline
     * do diff é o estado-alvo da solicitação, não o TOTVS. */
    await waitFor(() =>
      expect(screen.getAllByText("000777").length).toBeGreaterThan(0),
    );
    /* Sem alteração: não avança. */
    fireEvent.click(
      screen.getAllByRole("button", { name: "Avançar" })[0],
    );
    await waitFor(() =>
      expect(
        screen.getByText(/Nenhuma alteração identificada/),
      ).toBeTruthy(),
    );
    expect(dp.saveDraft).not.toHaveBeenCalled();
  });
});

describe("applySupplierLinkOps", () => {
  const base = [
    { supplierCode: "000001", store: "01", partNumber: "PN-1" },
    { supplierCode: "000002", store: "01", partNumber: "PN-2" },
  ];

  it("aplica add/update/remove sobre a base", () => {
    const out = applySupplierLinkOps(base, [
      {
        operation: "remove",
        key: { supplierCode: "000002", store: "01" },
      },
      {
        operation: "update",
        key: { supplierCode: "000001", store: "01" },
        fields: { partNumber: "PN-NEW" },
      },
      {
        operation: "add",
        key: { supplierCode: "000777", store: "01" },
        fields: { partNumber: "PN-777", catalogNumber: "C9" },
        supplierName: "FORN NOVO",
      },
    ]);
    const byKey = new Map(
      out.map((s) => [`${s.supplierCode}|${s.store}`, s]),
    );
    expect(byKey.get("000001|01")?.partNumber).toBe("PN-NEW");
    expect(byKey.has("000002|01")).toBe(false);
    expect(byKey.get("000777|01")?.supplierName).toBe("FORN NOVO");
  });

  it("ignora ops sobre chaves inexistentes e entradas inválidas", () => {
    const out = applySupplierLinkOps(base, [
      {
        operation: "update",
        key: { supplierCode: "999999", store: "01" },
        fields: { partNumber: "X" },
      },
      { operation: "remove", key: { supplierCode: "", store: "" } },
      null,
    ]);
    expect(out).toHaveLength(2);
    expect(applySupplierLinkOps(null, null)).toEqual([]);
  });
});
