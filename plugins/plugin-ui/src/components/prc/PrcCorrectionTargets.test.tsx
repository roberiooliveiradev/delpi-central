/** PRC-REF-023-GRANULAR-CORRECTION-09 — devolução granular (seletor do
 * analista) e correção granular (editor do solicitante).
 *
 * Cobertura:
 * - seletor: campos escalares + células de fornecedor por
 *   (supplierCode, store, atributo), motivo individual obrigatório,
 *   dedup de vínculo e payload do contrato oficial;
 * - editor: somente alvos devolvidos editáveis, motivo da Engenharia
 *   junto ao campo, modo changed/confirmed, endereçamento de todos os
 *   alvos e resumo antes do reenvio.
 * AuthZ/allowlist/CAS permanecem no backend — aqui é apresentação +
 * construção de payload do contrato. */

import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  PrcCorrectionTargetSelector,
  PrcReturnedFieldsEditor,
  buildReturnedChanges,
  correctionTargetsFromSelection,
  dedupeCorrectionLinks,
  emptyCorrectionSelection,
  fieldTargetsOf,
  hasSupplierTargets,
  returnedSupplierAttrMap,
  summarizeCorrectionSelection,
  type PrcCorrectionFieldOption,
  type PrcCorrectionLink,
  type PrcCorrectionSelection,
  type PrcCorrectionTargetWire,
} from "./PrcCorrectionTargets";

afterEach(cleanup);

const FIELDS: PrcCorrectionFieldOption[] = [
  { path: "description", label: "Descrição" },
  { path: "unit", label: "Unidade" },
  { path: "accountingAccount", label: "Conta contábil" },
];

const SUP_A: PrcCorrectionLink = {
  supplierCode: "000123",
  store: "01",
  supplierName: "Fornecedor A",
  supplierShortName: "F-A",
  partNumber: "PN-A",
  catalogNumber: "CAT-A",
};
const SUP_A2: PrcCorrectionLink = {
  ...SUP_A,
  store: "02",
  partNumber: "PN-A2",
};
const SUP_B: PrcCorrectionLink = {
  supplierCode: "000456",
  store: "01",
  supplierName: "Fornecedor B",
  partNumber: "PN-B",
  catalogNumber: "CAT-B",
};

const FIELD_TARGET: PrcCorrectionTargetWire = {
  targetType: "FIELD",
  targetPath: "description",
  reason: "Descrição abreviada incorreta.",
};
const PN_TARGET: PrcCorrectionTargetWire = {
  targetType: "SUPPLIER_LINK",
  targetPath: "suppliers",
  targetAttribute: "partNumber",
  supplierKey: { supplierCode: "000123", store: "01" },
  reason: "PN divergente do fabricante.",
};
const CAT_B_TARGET: PrcCorrectionTargetWire = {
  targetType: "SUPPLIER_LINK",
  targetPath: "suppliers",
  targetAttribute: "catalogNumber",
  supplierKey: { supplierCode: "000456", store: "01" },
  reason: "Catálogo errado.",
};
const LINK_TARGET: PrcCorrectionTargetWire = {
  targetType: "SUPPLIER_LINK",
  targetPath: "suppliers",
  targetAttribute: null,
  supplierKey: { supplierCode: "000123", store: "01" },
  reason: "Revise o vínculo completo.",
};

const DRAFT = {
  description: "CABO 2,5MM",
  unit: "PC",
  suppliers: [
    {
      supplierCode: "000123",
      store: "01",
      supplierName: "Fornecedor A",
      partNumber: "PN-A",
      catalogNumber: "CAT-A",
    },
    {
      supplierCode: "000456",
      store: "01",
      supplierName: "Fornecedor B",
      partNumber: "PN-B",
      catalogNumber: "CAT-B",
    },
  ],
};

function selectionWith(
  fields: Record<string, string>,
  suppliers: Record<
    string,
    Partial<{
      link: string;
      partNumber: string;
      catalogNumber: string;
    }>
  >,
): PrcCorrectionSelection {
  const sel = emptyCorrectionSelection();
  for (const [path, reason] of Object.entries(fields)) {
    sel.fields[path] = { selected: true, reason };
  }
  for (const [key, cells] of Object.entries(suppliers)) {
    sel.suppliers[key] = {
      link: {
        selected: cells.link !== undefined,
        reason: cells.link ?? "",
      },
      partNumber: {
        selected: cells.partNumber !== undefined,
        reason: cells.partNumber ?? "",
      },
      catalogNumber: {
        selected: cells.catalogNumber !== undefined,
        reason: cells.catalogNumber ?? "",
      },
    };
  }
  return sel;
}

/* ---------------------------------------------------------------- */
/* Helpers puros                                                     */
/* ---------------------------------------------------------------- */

describe("correctionTargetsFromSelection — payload oficial", () => {
  it("campo escalar vira FIELD com path e motivo", () => {
    const { targets } = correctionTargetsFromSelection(
      selectionWith({ description: "texto errado" }, {}),
      FIELDS,
      [SUP_A],
    );
    expect(targets).toEqual([
      {
        targetType: "FIELD",
        targetPath: "description",
        reason: "texto errado",
      },
    ]);
  });

  it("cada alvo tem motivo próprio — sem motivo genérico compartilhado", () => {
    const { targets, error } = correctionTargetsFromSelection(
      selectionWith(
        { description: "motivo A", unit: "motivo B" },
        { "000123|01": { partNumber: "motivo C" } },
      ),
      FIELDS,
      [SUP_A],
    );
    expect(error).toBe("");
    expect(targets).toHaveLength(3);
    expect(targets?.map((t) => t.reason)).toEqual([
      "motivo A",
      "motivo B",
      "motivo C",
    ]);
  });

  it("motivo ausente bloqueia e nomeia o alvo", () => {
    const { targets, error } = correctionTargetsFromSelection(
      selectionWith({ description: "motivo ok", unit: "" }, {}),
      FIELDS,
      [],
    );
    expect(targets).toBeNull();
    expect(error).toContain("Unidade");
  });

  it("célula de fornecedor vira SUPPLIER_LINK com identidade + atributo", () => {
    const { targets } = correctionTargetsFromSelection(
      selectionWith({}, { "000123|01": { partNumber: "pn errado" } }),
      FIELDS,
      [SUP_A],
    );
    expect(targets).toEqual([
      {
        targetType: "SUPPLIER_LINK",
        targetPath: "suppliers",
        targetAttribute: "partNumber",
        supplierKey: { supplierCode: "000123", store: "01" },
        reason: "pn errado",
      },
    ]);
  });

  it("vínculo integral sai com targetAttribute null", () => {
    const { targets } = correctionTargetsFromSelection(
      selectionWith({}, { "000123|01": { link: "revise tudo" } }),
      FIELDS,
      [SUP_A],
    );
    expect(targets?.[0].targetAttribute).toBeNull();
  });

  it("mesmo código em lojas diferentes gera alvos distintos", () => {
    const { targets } = correctionTargetsFromSelection(
      selectionWith(
        {},
        {
          "000123|01": { partNumber: "loja 01" },
          "000123|02": { partNumber: "loja 02" },
        },
      ),
      FIELDS,
      [SUP_A, SUP_A2],
    );
    expect(targets).toHaveLength(2);
    expect(targets?.map((t) => t.supplierKey?.store)).toEqual([
      "01",
      "02",
    ]);
  });

  it("dois fornecedores, atributos diferentes — alvos independentes", () => {
    const { targets } = correctionTargetsFromSelection(
      selectionWith(
        {},
        {
          "000123|01": { partNumber: "pn A" },
          "000456|01": { catalogNumber: "cat B" },
        },
      ),
      FIELDS,
      [SUP_A, SUP_B],
    );
    expect(targets).toHaveLength(2);
    expect(targets?.map((t) => t.targetAttribute)).toEqual([
      "partNumber",
      "catalogNumber",
    ]);
  });

  it("nenhum alvo selecionado bloqueia a devolução", () => {
    const { targets, error } = correctionTargetsFromSelection(
      emptyCorrectionSelection(),
      FIELDS,
      [SUP_A],
    );
    expect(targets).toBeNull();
    expect(error).toContain("ao menos um campo");
  });

  it("dedup por (code, store) preserva zeros à esquerda", () => {
    const links = dedupeCorrectionLinks([SUP_A, { ...SUP_A }, SUP_A2]);
    expect(links).toHaveLength(2);
    expect(links[0].supplierCode).toBe("000123");
  });

  it("resumo conta campos, fornecedores e atributos", () => {
    const summary = summarizeCorrectionSelection(
      selectionWith(
        { description: "m" },
        { "000123|01": { partNumber: "x", catalogNumber: "y" } },
      ),
      [SUP_A],
    );
    expect(summary.scalarFields).toBe(1);
    expect(summary.suppliers).toBe(1);
    expect(summary.supplierAttributes).toBe(2);
    expect(summary.totalTargets).toBe(3);
  });
});

describe("mapas de devolução — semântica dos alvos", () => {
  it("alvo sem atributo autoriza os dois atributos editáveis", () => {
    const map = returnedSupplierAttrMap([LINK_TARGET]);
    expect(map.get("000123|01")).toEqual(
      new Set(["partNumber", "catalogNumber"]),
    );
  });

  it("alvo de atributo autoriza apenas ele", () => {
    const map = returnedSupplierAttrMap([PN_TARGET]);
    expect(map.get("000123|01")).toEqual(new Set(["partNumber"]));
  });

  it("fieldTargetsOf/hasSupplierTargets separam os tipos", () => {
    const targets = [FIELD_TARGET, PN_TARGET];
    expect(fieldTargetsOf(targets)).toEqual([FIELD_TARGET]);
    expect(hasSupplierTargets(targets)).toBe(true);
    expect(hasSupplierTargets([FIELD_TARGET])).toBe(false);
  });
});

/* ---------------------------------------------------------------- */
/* buildReturnedChanges — payload do PATCH /returned-fields          */
/* ---------------------------------------------------------------- */

describe("buildReturnedChanges — correção do solicitante", () => {
  it("campo alterado sai changed e exige justificativa", () => {
    const { changes, error } = buildReturnedChanges({
      targets: [FIELD_TARGET],
      draft: DRAFT,
      supplierRows: [],
      fieldValues: { description: "CABO 4MM" },
      justifications: { description: "Ajustado conforme nota." },
    });
    expect(error).toBe("");
    expect(changes).toEqual([
      {
        path: "description",
        proposedValue: "CABO 4MM",
        reason: "Ajustado conforme nota.",
        mode: "changed",
      },
    ]);
  });

  it("campo alterado sem justificativa bloqueia", () => {
    const { changes, error } = buildReturnedChanges({
      targets: [FIELD_TARGET],
      draft: DRAFT,
      supplierRows: [],
      fieldValues: { description: "CABO 4MM" },
      justifications: {},
    });
    expect(changes).toBeNull();
    expect(error).toContain("justificativa");
  });

  it("campo mantido sai confirmed e endereça o alvo", () => {
    const { changes } = buildReturnedChanges({
      targets: [FIELD_TARGET],
      draft: DRAFT,
      supplierRows: [],
      fieldValues: {},
      justifications: {},
    });
    expect(changes?.[0].mode).toBe("confirmed");
    expect(changes?.[0].path).toBe("description");
  });

  it("fornecedores sem alteração: confirmed endereça todos os alvos", () => {
    const { changes } = buildReturnedChanges({
      targets: [PN_TARGET, CAT_B_TARGET],
      draft: DRAFT,
      supplierRows: [
        {
          rowId: "r1",
          origin: "draft",
          query: "",
          supplierCode: "000123",
          store: "01",
          supplierName: "Fornecedor A",
          partNumber: "PN-A",
          catalogNumber: "CAT-A",
        },
        {
          rowId: "r2",
          origin: "draft",
          query: "",
          supplierCode: "000456",
          store: "01",
          supplierName: "Fornecedor B",
          partNumber: "PN-B",
          catalogNumber: "CAT-B",
        },
      ],
      fieldValues: {},
      justifications: {},
    });
    expect(changes).toHaveLength(1);
    expect(changes?.[0].path).toBe("suppliers");
    expect(changes?.[0].mode).toBe("confirmed");
  });

  it("mudança parcial emite changed + confirmed (vínculos mantidos)", () => {
    const { changes } = buildReturnedChanges({
      targets: [PN_TARGET, CAT_B_TARGET],
      draft: DRAFT,
      supplierRows: [
        {
          rowId: "r1",
          origin: "draft",
          query: "",
          supplierCode: "000123",
          store: "01",
          supplierName: "Fornecedor A",
          partNumber: "PN-A-NOVO",
          catalogNumber: "CAT-A",
        },
        {
          rowId: "r2",
          origin: "draft",
          query: "",
          supplierCode: "000456",
          store: "01",
          supplierName: "Fornecedor B",
          partNumber: "PN-B",
          catalogNumber: "CAT-B",
        },
      ],
      fieldValues: {},
      justifications: {},
      supplierJustification: "PN corrigido no cadastro.",
    });
    expect(changes).toHaveLength(2);
    expect(changes?.[0].mode).toBe("changed");
    expect(changes?.[1].mode).toBe("confirmed");
  });

  it("vínculo alterado exige Part Number", () => {
    const { changes, error } = buildReturnedChanges({
      targets: [PN_TARGET],
      draft: DRAFT,
      supplierRows: [
        {
          rowId: "r1",
          origin: "draft",
          query: "",
          supplierCode: "000123",
          store: "01",
          supplierName: "Fornecedor A",
          partNumber: "",
          catalogNumber: "CAT-A-X",
        },
      ],
      fieldValues: {},
      justifications: {},
      supplierJustification: "ok",
    });
    expect(changes).toBeNull();
    expect(error).toContain("Part Number");
  });

  it("mudança de fornecedor exige justificativa", () => {
    const { changes, error } = buildReturnedChanges({
      targets: [PN_TARGET],
      draft: DRAFT,
      supplierRows: [
        {
          rowId: "r1",
          origin: "draft",
          query: "",
          supplierCode: "000123",
          store: "01",
          supplierName: "Fornecedor A",
          partNumber: "PN-NOVO",
          catalogNumber: "CAT-A",
        },
      ],
      fieldValues: {},
      justifications: {},
    });
    expect(changes).toBeNull();
    expect(error).toContain("justificativa");
  });
});

/* ---------------------------------------------------------------- */
/* Seletor — renderização                                            */
/* ---------------------------------------------------------------- */

describe("PrcCorrectionTargetSelector — renderização", () => {
  function renderSelector(suppliers: PrcCorrectionLink[] = [SUP_A, SUP_B]) {
    let last: PrcCorrectionSelection = emptyCorrectionSelection();
    const utils = render(
      <PrcCorrectionTargetSelector
        fieldOptions={FIELDS}
        suppliers={suppliers}
        selection={last}
        onChange={(n) => {
          last = n;
        }}
      />,
    );
    return { ...utils, getSelection: () => last };
  }

  it("campo escalar: checkbox + editor de motivo ao selecionar", () => {
    const { getSelection } = renderSelector();
    const box = document.getElementById(
      "prc-return-field-description",
    ) as HTMLInputElement;
    fireEvent.click(box);
    expect(getSelection().fields.description.selected).toBe(true);
  });

  it("tabela de fornecedores tem uma célula por atributo elegível", () => {
    renderSelector();
    expect(
      document.getElementById(
        "prc-return-sup-000123-01-partNumber",
      ),
    ).toBeTruthy();
    expect(
      document.getElementById(
        "prc-return-sup-000456-01-catalogNumber",
      ),
    ).toBeTruthy();
    expect(
      document.getElementById("prc-return-sup-000123-01-link"),
    ).toBeTruthy();
  });

  it("selecionar célula registra identidade (code,store) — não índice", () => {
    const { getSelection } = renderSelector();
    fireEvent.click(
      document.getElementById(
        "prc-return-sup-000456-01-partNumber",
      ) as HTMLElement,
    );
    expect(
      getSelection().suppliers["000456|01"].partNumber.selected,
    ).toBe(true);
    expect(getSelection().suppliers["000123|01"]).toBeUndefined();
  });

  it("motivo por célula: textarea renderizado para o alvo selecionado", () => {
    let last = emptyCorrectionSelection();
    const onChange = (n: PrcCorrectionSelection) => {
      last = n;
    };
    const utils = render(
      <PrcCorrectionTargetSelector
        fieldOptions={FIELDS}
        suppliers={[SUP_A]}
        selection={last}
        onChange={onChange}
      />,
    );
    fireEvent.click(
      document.getElementById(
        "prc-return-sup-000123-01-partNumber",
      ) as HTMLElement,
    );
    // Componente controlado: re-render com a seleção atualizada.
    utils.rerender(
      <PrcCorrectionTargetSelector
        fieldOptions={FIELDS}
        suppliers={[SUP_A]}
        selection={last}
        onChange={onChange}
      />,
    );
    const reason = document.getElementById(
      "prc-return-reason-sup-000123-01-partNumber",
    ) as HTMLTextAreaElement;
    expect(reason).toBeTruthy();
    fireEvent.change(reason, { target: { value: "pn errado" } });
    expect(
      last.suppliers["000123|01"].partNumber.reason,
    ).toBe("pn errado");
  });
});

/* ---------------------------------------------------------------- */
/* Editor — renderização do card do solicitante                      */
/* ---------------------------------------------------------------- */

describe("PrcReturnedFieldsEditor — correção granular", () => {
  const SPECS = [
    { path: "description", kind: "text", maxLength: 120 },
    { path: "unit", kind: "select", enumValues: ["PC", "CX", "KG"] },
  ];

  it("mostra motivo da Engenharia e valor atual junto ao campo", () => {
    render(
      <PrcReturnedFieldsEditor
        targets={[FIELD_TARGET]}
        fieldSpecs={SPECS}
        draft={DRAFT}
        onSubmit={vi.fn()}
      />,
    );
    expect(
      screen.getByText(/Descrição abreviada incorreta/),
    ).toBeTruthy();
    expect(
      screen.getAllByText(/CABO 2,5MM/).length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("somente o atributo devolvido é editável; o irmão fica readonly", () => {
    render(
      <PrcReturnedFieldsEditor
        targets={[PN_TARGET]}
        fieldSpecs={SPECS}
        draft={DRAFT}
        onSubmit={vi.fn()}
      />,
    );
    const pn = document.getElementById(
      "prc-correct-sup-000123-01-partNumber",
    ) as HTMLInputElement;
    expect(pn).toBeTruthy();
    // Catálogo do mesmo vínculo não foi devolvido → texto, sem input.
    expect(
      document.getElementById(
        "prc-correct-sup-000123-01-catalogNumber",
      ),
    ).toBeNull();
  });

  it("fornecedor alheio não tem nenhuma célula editável", () => {
    render(
      <PrcReturnedFieldsEditor
        targets={[PN_TARGET]}
        fieldSpecs={SPECS}
        draft={DRAFT}
        onSubmit={vi.fn()}
      />,
    );
    expect(
      document.getElementById(
        "prc-correct-sup-000456-01-partNumber",
      ),
    ).toBeNull();
    expect(
      document.getElementById(
        "prc-correct-sup-000456-01-catalogNumber",
      ),
    ).toBeNull();
  });

  it("vínculo integral devolvido libera os dois atributos", () => {
    render(
      <PrcReturnedFieldsEditor
        targets={[LINK_TARGET]}
        fieldSpecs={SPECS}
        draft={DRAFT}
        onSubmit={vi.fn()}
      />,
    );
    expect(
      document.getElementById(
        "prc-correct-sup-000123-01-partNumber",
      ),
    ).toBeTruthy();
    expect(
      document.getElementById(
        "prc-correct-sup-000123-01-catalogNumber",
      ),
    ).toBeTruthy();
  });

  it("submit entrega changes cobrindo todos os alvos", () => {
    const onSubmit = vi.fn();
    render(
      <PrcReturnedFieldsEditor
        targets={[FIELD_TARGET, PN_TARGET]}
        fieldSpecs={SPECS}
        draft={DRAFT}
        onSubmit={onSubmit}
      />,
    );
    // Altera PN autorizado + justifica.
    fireEvent.change(
      document.getElementById(
        "prc-correct-sup-000123-01-partNumber",
      ) as HTMLElement,
      { target: { value: "PN-NOVO" } },
    );
    fireEvent.change(
      document.getElementById(
        "prc-correct-justify-suppliers",
      ) as HTMLElement,
      { target: { value: "PN corrigido conforme datasheet." } },
    );
    // Campo escalar sem alteração → justificativa opcional (confirmed).
    fireEvent.click(
      screen.getByText("Salvar correções e reenviar"),
    );
    expect(onSubmit).toHaveBeenCalledTimes(1);
    const changes = onSubmit.mock.calls[0][0] as Array<{
      path: string;
      mode: string;
    }>;
    // FIELD confirmed + suppliers changed + suppliers confirmed.
    expect(changes).toHaveLength(3);
    expect(changes.map((c) => c.mode)).toEqual([
      "confirmed",
      "changed",
      "confirmed",
    ]);
  });

  it("resumo exibe antes → depois dos alvos devolvidos", () => {
    render(
      <PrcReturnedFieldsEditor
        targets={[FIELD_TARGET]}
        fieldSpecs={SPECS}
        draft={DRAFT}
        onSubmit={vi.fn()}
      />,
    );
    const review = screen.getByText(/Resumo antes do reenvio/);
    expect(review).toBeTruthy();
    // Valor atual aparece no campo e no resumo — múltiplas ocorrências.
    expect(
      screen.getAllByText(/CABO 2,5MM/).length,
    ).toBeGreaterThanOrEqual(2);
  });

  it("identidade do vínculo nunca vira input", () => {
    const { container } = render(
      <PrcReturnedFieldsEditor
        targets={[LINK_TARGET]}
        fieldSpecs={SPECS}
        draft={DRAFT}
        onSubmit={vi.fn()}
      />,
    );
    const row = container.querySelector('tr[data-link-key="000123|01"]')!;
    const scoped = within(row as HTMLElement);
    // Código/loja/razão social/fantasia são texto, não inputs.
    expect(scoped.getByText("000123")).toBeTruthy();
    expect(scoped.getByText("Fornecedor A")).toBeTruthy();
    const inputs = row.querySelectorAll("input");
    // Somente PN + Catálogo editáveis.
    expect(inputs).toHaveLength(2);
  });
});
