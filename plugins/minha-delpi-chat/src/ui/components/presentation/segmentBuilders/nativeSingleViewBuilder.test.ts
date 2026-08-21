import { describe, expect, it } from "vitest";

import { buildNativeSingleViewSegments } from "./nativeSingleViewBuilder";
import type { AssistantContentSegment } from "../../message/assistantContentTypes";
import { getPresentationInsightFromToolCalls } from "../presentationMetadataReaders";

describe("buildNativeSingleViewSegments", () => {
  it("inclui todas as tabelas quando renderPlan aponta tablePresentations", () => {
    const visuals: AssistantContentSegment[] = [
      {
        kind: "table",
        presentation: {
          type: "table",
          title: "Estrutura do produto (BOM)",
          role: "structure",
          columns: [],
          rows: [{ component_code: "50250258" }],
        },
      },
      {
        kind: "table",
        presentation: {
          type: "table",
          title: "Fornecedores por matéria-prima",
          role: "list",
          columns: [],
          rows: [{ supplier_code: "000052" }],
        },
      },
      {
        kind: "table",
        presentation: {
          type: "table",
          title: "Última compra por matéria-prima",
          role: "list",
          columns: [],
          rows: [{ invoice_number: "015277" }],
        },
      },
    ];
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          explicitSessionFormat: "table",
          presentationDecision: {
            selected: "table",
            layoutMode: "single",
          },
          renderPlan: {
            version: 1,
            layoutMode: "single",
            segments: [
              {
                kind: "table",
                slot: "operationalTables",
                source: "tablePresentations",
              },
            ],
          },
        },
      },
    ] as never;

    const segments = buildNativeSingleViewSegments("", toolCalls, visuals);
    const tableTitles = (segments ?? [])
      .filter((segment) => segment.kind === "table")
      .map((segment) => segment.presentation.title);

    expect(tableTitles).toEqual([
      "Estrutura do produto (BOM)",
      "Fornecedores por matéria-prima",
      "Última compra por matéria-prima",
    ]);
  });

  it("honra lead markdown do renderPlan com selected=table (llmProseDecoupled)", () => {
    const lead =
      "Saldo disponível total: **0** un. em **4** posição(ões). **4** posição(ões) com disponível zerado.";
    const visuals: AssistantContentSegment[] = [
      {
        kind: "table",
        presentation: {
          type: "table",
          title: "Estoque do produto",
          columns: [{ key: "branch", label: "Filial" }],
          rows: [{ branch: "01", available_quantity: 0 }],
        },
      },
    ];
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          llmProseDecoupled: true,
          dataOnlyPresentation: true,
          proseDeliveryMode: "llm",
          textPresentation: {
            type: "markdown",
            markdown: "",
            title: "Resultado da consulta",
          },
          presentationDecision: {
            selected: "table",
            layoutMode: "single",
            proseSource: "llm",
            insight:
              "A tabela lista os principais registros encontrados (4 linhas).",
          },
          renderPlan: {
            version: 1,
            layoutMode: "single",
            segments: [
              { kind: "markdown", slot: "lead", source: "assistantMessage" },
              { kind: "table", slot: "primary", source: "tablePresentation" },
            ],
          },
          tablePresentation: {
            type: "table",
            title: "Estoque do produto",
            columns: [{ key: "branch", label: "Filial" }],
            rows: [{ branch: "01", available_quantity: 0 }],
          },
        },
      },
    ] as never;

    const segments = buildNativeSingleViewSegments(lead, toolCalls, visuals) ?? [];
    const markdown = segments
      .filter((segment) => segment.kind === "markdown")
      .map((segment) => ("markdown" in segment ? segment.markdown : ""))
      .join("\n");

    expect(markdown).toContain("Saldo disponível total");
    expect(segments.some((segment) => segment.kind === "table")).toBe(true);
    expect(getPresentationInsightFromToolCalls(toolCalls)).toBe("");
  });
});
