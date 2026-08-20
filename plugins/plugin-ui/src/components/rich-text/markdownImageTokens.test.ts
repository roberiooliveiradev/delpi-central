import { describe, expect, it } from "vitest";

import {
  listInlineAttachmentIdsFromMarkdown,
  listInlinePendingIdsFromMarkdown,
  parseMarkdownImages,
  rewriteInlinePendingInMarkdown,
} from "./markdownImageTokens";

describe("parseMarkdownImages", () => {
  it("separa href do title (align legado no title)", () => {
    const tokens = parseMarkdownImages(
      'ola ![a](attachment:pending:x "align=center") fim',
    );
    expect(tokens).toHaveLength(1);
    expect(tokens[0]?.href).toBe("attachment:pending:x");
    expect(tokens[0]?.title).toBe("align=center");
    expect(tokens[0]?.alt).toBe("a");
  });

  it("aceita title com aspas simples", () => {
    const tokens = parseMarkdownImages("![b](attachment:pending:y 'align=right')");
    expect(tokens[0]?.href).toBe("attachment:pending:y");
    expect(tokens[0]?.title).toBe("align=right");
  });

  it("href limpo sem title", () => {
    const tokens = parseMarkdownImages(
      "![c](attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee)",
    );
    expect(tokens[0]?.href).toBe(
      "attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    );
    expect(tokens[0]?.title).toBe("");
  });
});

describe("listInlinePendingIdsFromMarkdown", () => {
  it("não inclui title no pending id", () => {
    expect(
      listInlinePendingIdsFromMarkdown(
        '![a](attachment:pending:x "align=center") ![b](attachment:pending:z)',
      ),
    ).toEqual(["x", "z"]);
  });
});

describe("listInlineAttachmentIdsFromMarkdown", () => {
  it("lista só uuid persistido", () => {
    const md =
      '![a](attachment:pending:p1) ![b](attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee "align=center")';
    expect(listInlineAttachmentIdsFromMarkdown(md)).toEqual([
      "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    ]);
  });
});

describe("rewriteInlinePendingInMarkdown", () => {
  it("reescreve pending com title e remove title do token", () => {
    const out = rewriteInlinePendingInMarkdown(
      '<p style="text-align:center">x ![s](attachment:pending:local-1 "align=center") y</p>',
      { "local-1": "11111111-2222-3333-4444-555555555555" },
    );
    expect(out).toBe(
      '<p style="text-align:center">x ![s](attachment:11111111-2222-3333-4444-555555555555) y</p>',
    );
  });

  it("preserva tokens não mapeados", () => {
    expect(
      rewriteInlinePendingInMarkdown("![a](attachment:pending:missing)", {
        other: "uuid",
      }),
    ).toBe("![a](attachment:pending:missing)");
  });
});
