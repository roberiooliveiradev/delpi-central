#!/usr/bin/env npx tsx
import {
  getDataCoverageNoticeFromToolCalls,
  getPresentationPairFromToolCalls,
  getTablePresentationFromPair,
  getTreePresentationFromPair,
  resolvePresentationLayoutMode,
  shouldShowRichPresentation,
  shouldSuppressMarkdownForPresentation,
} from "../src/ui/components/chatPresentation";

const parentsToolCalls = [
  {
    name: "execute_external_action",
    metadata: {
      ok: true,
      path: "/products/10080022/parents",
      textPresentation: {
        type: "markdown",
        title: "Onde é usado o produto 10080022",
        markdown:
          "### Onde é usado o produto 10080022\n\nProduto consultado: **10080022** — TERM. OLHAL M5.\n\nForam encontrados **419** produto(s) pai na API.\n\nEsta resposta traz **50** vínculo(s) nesta página/consulta.\n\nUse a **árvore** ou a **tabela** abaixo para explorar onde o item é usado.",
      },
      dataCoverageNotice: {
        kind: "pagination",
        message:
          "Produtos pai parcial: página 1 de 9 (50 de 419 registro(s) nesta resposta).",
      },
      treePresentation: {
        type: "tree",
        title: "Onde é usado o produto 10080022",
        root: {
          id: "10080022",
          label: "10080022",
          children: [{ id: "23-011", label: "23-011", children: [] }],
        },
      },
      tablePresentation: {
        type: "table",
        title: "Produtos pai (onde é usado)",
        columns: [
          { key: "code", label: "Código" },
          { key: "description", label: "Descrição" },
        ],
        rows: Array.from({ length: 50 }, (_, index) => ({
          code: `50211${String(index).padStart(3, "0")}`,
          description: `Item ${index + 1}`,
        })),
      },
    },
  },
];

const pair = getPresentationPairFromToolCalls(parentsToolCalls);
const layout = resolvePresentationLayoutMode(parentsToolCalls, pair);
const notice = getDataCoverageNoticeFromToolCalls(parentsToolCalls);
const table = getTablePresentationFromPair(pair);
const tree = getTreePresentationFromPair(pair);

const checks: Array<[string, boolean]> = [
  ["layout commentary-visual", layout === "commentary-visual"],
  ["coverage notice with 50", notice?.message.includes("50") ?? false],
  ["table rows count 50", table?.rows.length === 50],
  ["tree presentation present", Boolean(tree?.root)],
  ["rich presentation enabled", shouldShowRichPresentation("", parentsToolCalls)],
  [
    "suppress duplicate markdown",
    shouldSuppressMarkdownForPresentation(
      "Onde é usado o produto 10080022",
      pair,
      parentsToolCalls,
    ),
  ],
];

let failed = 0;

for (const [label, ok] of checks) {
  console.log(`${ok ? "PASS" : "FAIL"} ${label}`);
  if (!ok) failed += 1;
}

if (failed > 0) {
  process.exit(1);
}

console.log("Frontend pagination presentation checks OK");
