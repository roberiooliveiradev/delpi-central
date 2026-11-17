/** PRC-DESCRIPTION-REQUIRED — descrição obrigatória no CREATE e
 * não-zerável em edição; ``allowBlank`` do catálogo preserva
 * ``customerReference`` vazio sem endurecer campos text opcionais. */

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
  sources: ["my-requests"],
  editableDraftPaths: ["description", "customerReference", "unit"],
  supplierKeys: { required: ["supplierCode"], optional: [] },
  fields: [
    {
      path: "customerReference",
      kind: "text",
      requiredCreateIntake: true,
      allowBlank: true,
      verifiable: true,
      maxLength: 60,
    },
    {
      path: "description",
      kind: "text",
      requiredCreateIntake: true,
      verifiable: true,
      maxLength: 200,
    },
    {
      path: "unit",
      kind: "enum",
      requiredCreateIntake: true,
      verifiable: true,
      enumValues: ["UN", "KG"],
      maxLength: 3,
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

const editCaseProps = {
  requestId: "req-1",
  expectedVersion: 3,
  requestType: "create" as const,
  draft: CREATE_DRAFT,
};

function renderEditCase(dp: ReturnType<typeof provider>) {
  return render(
    <PrcRequestForm
      source="my-requests"
      dataProvider={dp as never}
      onCancel={() => undefined}
      onCompleted={() => undefined}
      editCase={editCaseProps}
    />,
  );
}

describe("PrcRequestForm — descrição obrigatória", () => {
  it("CREATE: bloqueia Avançar com descrição vazia (allowBlank poupa referência)", async () => {
    const dp = provider();
    render(
      <PrcRequestForm
        source="my-requests"
        dataProvider={dp as never}
        onCancel={() => undefined}
        onCompleted={() => undefined}
      />,
    );
    // identify → sheet (create é o requestType default).
    await waitFor(() => screen.getAllByText("O que precisa ser feito?"));
    fireEvent.click(
      screen.getAllByRole("button", { name: "Avançar" })[0],
    );
    await waitFor(() =>
      expect(
        document.getElementById("prc-new-description"),
      ).toBeTruthy(),
    );
    fireEvent.click(
      screen.getAllByRole("button", { name: "Avançar" })[0],
    );
    await waitFor(() =>
      expect(screen.getByText(/Preencha «Descrição»/)).toBeTruthy(),
    );
    // customerReference allowBlank nunca é o campo apontado no erro.
    expect(
      screen.queryByText(/Preencha «Referência do cliente»/),
    ).toBeNull();
    expect(dp.submitIntake).not.toHaveBeenCalled();
  });

  it("edição: zerar a descrição bloqueia Avançar e não chama saveDraft", async () => {
    const dp = provider();
    renderEditCase(dp);
    await waitFor(() => screen.getAllByDisplayValue("RESINA EPOXI"));
    const desc = document.getElementById(
      "prc-new-description",
    ) as HTMLInputElement;
    fireEvent.change(desc, { target: { value: "   " } });
    fireEvent.click(
      screen.getAllByRole("button", { name: "Avançar" })[0],
    );
    await waitFor(() =>
      expect(screen.getByText(/Preencha «Descrição»/)).toBeTruthy(),
    );
    expect(dp.saveDraft).not.toHaveBeenCalled();
  });

  it("edição: alterar outros campos sem tocar a descrição avança", async () => {
    const dp = provider();
    renderEditCase(dp);
    await waitFor(() => screen.getAllByDisplayValue("RESINA EPOXI"));
    const ref = document.getElementById(
      "prc-new-customerReference",
    ) as HTMLInputElement;
    fireEvent.change(ref, { target: { value: "REF-77" } });
    fireEvent.click(
      screen.getAllByRole("button", { name: "Avançar" })[0],
    );
    await waitFor(() =>
      expect(
        screen.queryByText(/Preencha «Descrição»/),
      ).toBeNull(),
    );
  });
});
