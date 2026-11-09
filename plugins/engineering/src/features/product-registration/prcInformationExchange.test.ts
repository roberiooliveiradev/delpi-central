import { describe, expect, it } from "vitest";

import type {
  PrcFieldSpec,
  PrcInformationQuestion,
  PrcInformationRound,
} from "./api/productRegistrationApi";
import {
  allInformationQuestionsAccepted,
  buildAnswerInputs,
  buildQuestionInputs,
  emptyInfoQuestion,
  findActiveInformationRound,
  followUpInputFor,
  informationRoundConflictMessage,
  initialInfoRoleView,
  isRequesterSubject,
  pendingFieldsFromDrafts,
  questionableFieldSpecs,
  resolvedInformationRounds,
  supplierOptionsFromTechnicalDraft,
  validateInfoAnswersForSubmit,
  validateInfoQuestions,
} from "./prcInformationExchange";

function spec(path: string, kind = "string"): PrcFieldSpec {
  return {
    path,
    kind,
    requiredCreateIntake: false,
    verifiable: true,
    maxLength: 100,
  };
}

function question(
  partial: Partial<PrcInformationQuestion> & { id: string },
): PrcInformationQuestion {
  return {
    targetType: "GENERAL",
    questionText: "q",
    status: "pending",
    ...partial,
  };
}

function round(
  partial: Partial<PrcInformationRound> & { id: string },
): PrcInformationRound {
  return {
    requestId: "r",
    status: "awaiting_requester",
    version: 1,
    questions: [],
    ...partial,
  };
}

describe("prcInformationExchange — PRC-REF-019", () => {
  it("valida ao menos uma pergunta com texto (positivo/negativo)", () => {
    expect(validateInfoQuestions([]).valid).toBe(false);

    const blank = emptyInfoQuestion();
    const bad = validateInfoQuestions([blank]);
    expect(bad.valid).toBe(false);
    expect(bad.rowErrors[blank.rowId]).toMatch(/Escreva a pergunta/);

    const ok = { ...emptyInfoQuestion(), questionText: "  Qual a NCM?  " };
    expect(validateInfoQuestions([ok]).valid).toBe(true);
  });

  it("FIELD exige campo; SUPPLIER_LINK exige código e loja", () => {
    const field = {
      ...emptyInfoQuestion("FIELD"),
      questionText: "Confirme",
    };
    expect(validateInfoQuestions([field]).rowErrors[field.rowId]).toMatch(
      /campo/i,
    );
    const supplier = {
      ...emptyInfoQuestion("SUPPLIER_LINK"),
      questionText: "Confirme",
      supplierCode: "000123",
    };
    expect(validateInfoQuestions([supplier]).rowErrors[supplier.rowId]).toMatch(
      /loja/i,
    );
  });

  it("alvo FIELD duplicado é recusado; GENERAL repetido é permitido", () => {
    const a = {
      ...emptyInfoQuestion("FIELD"),
      targetPath: "description",
      questionText: "a",
    };
    const b = { ...a, rowId: "other", questionText: "b" };
    expect(validateInfoQuestions([a, b]).valid).toBe(false);

    const g1 = { ...emptyInfoQuestion(), questionText: "a" };
    const g2 = { ...emptyInfoQuestion(), questionText: "b" };
    expect(validateInfoQuestions([g1, g2]).valid).toBe(true);
  });

  it("monta o payload tipado e deriva pendingFields só de FIELD", () => {
    const drafts = [
      {
        ...emptyInfoQuestion("FIELD"),
        targetPath: "description",
        questionText: " Descrição? ",
      },
      {
        ...emptyInfoQuestion("SUPPLIER_LINK"),
        supplierCode: " 000123 ",
        store: "01",
        targetAttribute: "catalogNumber" as const,
        questionText: "Catálogo?",
      },
      { ...emptyInfoQuestion(), questionText: "Geral" },
    ];
    expect(buildQuestionInputs(drafts)).toEqual([
      { targetType: "FIELD", targetPath: "description", questionText: "Descrição?" },
      {
        targetType: "SUPPLIER_LINK",
        targetAttribute: "catalogNumber",
        supplierKey: { supplierCode: "000123", store: "01" },
        questionText: "Catálogo?",
      },
      { targetType: "GENERAL", questionText: "Geral" },
    ]);
    expect(pendingFieldsFromDrafts(drafts)).toEqual(["description"]);
  });

  it("catálogo de alvos exclui código oficial e agregado de fornecedores", () => {
    const out = questionableFieldSpecs([
      spec("officialProductCode"),
      spec("description"),
      spec("suppliers", "suppliers"),
      spec("unit"),
    ]);
    expect(out.map((s) => s.path)).toEqual(["description", "unit"]);
    expect(questionableFieldSpecs(null)).toEqual([]);
  });

  it("extrai fornecedores únicos da ficha técnica", () => {
    const out = supplierOptionsFromTechnicalDraft({
      suppliers: [
        { supplierCode: "000123", store: "01", supplierName: "ACME" },
        { supplierCode: "000123", store: "01", supplierName: "ACME" },
        { supplierCode: "", store: "01" },
      ],
    });
    expect(out).toEqual([
      { supplierCode: "000123", store: "01", supplierName: "ACME" },
    ]);
    expect(supplierOptionsFromTechnicalDraft(null)).toEqual([]);
  });

  it("envio de respostas exige texto em todas as perguntas", () => {
    const qs = [question({ id: "a" }), question({ id: "b" })];
    const bad = validateInfoAnswersForSubmit(qs, { a: "ok", b: "  " });
    expect(bad.valid).toBe(false);
    expect(Object.keys(bad.errors)).toEqual(["b"]);
    expect(validateInfoAnswersForSubmit(qs, { a: "x", b: "y" }).valid).toBe(
      true,
    );
    expect(buildAnswerInputs(qs, { a: " x " })).toEqual([
      { questionId: "a", text: "x" },
      { questionId: "b", text: "" },
    ]);
  });

  it("complemento mantém o alvo da pergunta original", () => {
    expect(
      followUpInputFor(
        question({
          id: "q",
          targetType: "FIELD",
          targetPath: "unit",
        }),
        " Qual unidade? ",
      ),
    ).toEqual({
      targetType: "FIELD",
      targetPath: "unit",
      questionText: "Qual unidade?",
    });
    expect(
      followUpInputFor(question({ id: "q" }), "Mais detalhes").targetType,
    ).toBe("GENERAL");
  });

  it("separa rodada ativa das resolvidas e detecta aceite total", () => {
    const rounds = [
      round({ id: "1", sequence: 1, status: "resolved" }),
      round({ id: "2", sequence: 2, status: "awaiting_review" }),
    ];
    expect(findActiveInformationRound(rounds)?.id).toBe("2");
    expect(resolvedInformationRounds(rounds).map((r) => r.id)).toEqual(["1"]);
    expect(findActiveInformationRound([rounds[0]])).toBeNull();

    expect(allInformationQuestionsAccepted([])).toBe(false);
    expect(
      allInformationQuestionsAccepted([
        question({ id: "a", status: "accepted" }),
        question({ id: "b", status: "submitted" }),
      ]),
    ).toBe(false);
    expect(
      allInformationQuestionsAccepted([
        question({ id: "a", status: "accepted" }),
      ]),
    ).toBe(true);
  });

  it("FIX-01: identidade fail-closed e visão dual-role", () => {
    expect(isRequesterSubject(null, "a")).toBe(false);
    expect(isRequesterSubject("a", "a")).toBe(true);
    expect(
      initialInfoRoleView({
        isRequester: true,
        canRespond: true,
        canReview: true,
        activeRoundStatus: "awaiting_requester",
      }),
    ).toBe("requester");
    expect(
      informationRoundConflictMessage(
        "409 information_round_open",
        "Aguarde.",
      ),
    ).toBe("Aguarde.");
  });
});
