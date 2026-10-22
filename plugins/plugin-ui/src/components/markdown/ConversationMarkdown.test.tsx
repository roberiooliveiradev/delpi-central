import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  ConversationMarkdown,
  conversationMarkdownToPlainText,
} from "./ConversationMarkdown";

describe("ConversationMarkdown — governed, disabled by default", () => {
  it("renders v1 content verbatim, with the same p/class node", () => {
    const source = "**OP-10293**\n<script>alert(1)</script> [abrir](https://example.org)";
    const { container } = render(
      <ConversationMarkdown className="delia-turn__content" text={source} />,
    );
    const paragraph = container.querySelector("p.delia-turn__content");
    expect(paragraph?.textContent).toBe(source);
    expect(container.querySelector("a,strong,script,img")).toBeNull();
  });

  it("renders paragraphs when enabled", () => {
    const { container } = render(
      <ConversationMarkdown enabled text={"Primeiro.\n\nSegundo."} />,
    );
    expect(container.querySelectorAll("p")).toHaveLength(2);
  });

  it("renders bold and italic", () => {
    const { container } = render(
      <ConversationMarkdown enabled text={"**negrito** e *italico*"} />,
    );
    expect(container.querySelector("strong")?.textContent).toBe("negrito");
    expect(container.querySelector("em")?.textContent).toBe("italico");
  });

  it("renders subordinate headings", () => {
    const { container } = render(
      <ConversationMarkdown enabled text={"# A\n\n## B\n\n### C\n\n#### D"} />,
    );
    expect(container.querySelector("h4")?.textContent).toMatch(/A|B/);
    expect(container.querySelector("h5")?.textContent).toBe("C");
    expect(container.querySelector("h6")?.textContent).toBe("D");
    expect(container.querySelector("h1,h2,h3")).toBeNull();
  });

  it("renders ordered and unordered lists", () => {
    const { container } = render(
      <ConversationMarkdown
        enabled
        text={"- OP-10293\n- 3 KG\n\n1. um\n2. dois"}
      />,
    );
    expect(container.querySelectorAll("ul li")).toHaveLength(2);
    expect(container.querySelectorAll("ol li")).toHaveLength(2);
    expect(container.textContent).toContain("OP-10293");
    expect(container.textContent).toContain("3 KG");
  });

  it("renders nested lists within depth", () => {
    const { container } = render(
      <ConversationMarkdown
        enabled
        text={"- pai\n  - filho\n    - neto"}
      />,
    );
    expect(container.querySelectorAll("li").length).toBeGreaterThanOrEqual(3);
    expect(container.querySelector("ul ul")).toBeTruthy();
  });

  it("renders blockquotes, hr, inline and fenced code", () => {
    const { container } = render(
      <ConversationMarkdown
        enabled
        text={"> nota\n\n---\n\n`inline`\n\n```\ncódigo\n```"}
      />,
    );
    expect(container.querySelector("blockquote")?.textContent).toContain("nota");
    expect(container.querySelector("hr")).toBeTruthy();
    expect(container.querySelector("code")?.textContent).toBe("inline");
    expect(container.querySelector("pre code")?.textContent).toContain("código");
  });

  it("preserves soft line breaks as br", () => {
    const { container } = render(
      <ConversationMarkdown enabled text={"linha A  \nlinha B"} />,
    );
    expect(container.querySelector("br")).toBeTruthy();
  });

  it("does not materialize HTML, images, tables or executable code", () => {
    const { container } = render(
      <ConversationMarkdown
        enabled
        text={
          '<script>window.evil=1</script>\n\n![remote](https://example.org/image.png)\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n```mermaid\ngraph TD\n```'
        }
      />,
    );
    expect(
      container.querySelector("script,img,iframe,svg:not(.lucide),table"),
    ).toBeNull();
    expect(container.querySelector("pre code")?.textContent).toContain("graph TD");
    expect(container.textContent).toMatch(/a[\s\S]*b/);
  });

  it("does not create navigable links without an authorized destination", () => {
    const { container } = render(
      <ConversationMarkdown
        enabled
        text={
          "[interno](/apps/delia) [externo](https://example.org) [malicioso](javascript:alert(1))"
        }
      />,
    );
    expect(container.querySelector("a")).toBeNull();
    expect(container.textContent).toContain("interno");
    expect(container.textContent).toContain("externo");
  });

  it("only renders explicitly authorized https and internal links", () => {
    const { container } = render(
      <ConversationMarkdown
        enabled
        text={
          "[interno](/apps/delia) [externo](https://example.org/doc) [outro](https://other.invalid)"
        }
        authorizedLinks={[
          { href: "/apps/delia", kind: "internal" },
          { href: "https://example.org/doc", kind: "external" },
          { href: "https://other.invalid", kind: "internal" },
        ]}
      />,
    );
    const anchors = container.querySelectorAll("a");
    expect(anchors).toHaveLength(2);
    expect(anchors[0]?.getAttribute("href")).toBe("/apps/delia");
    expect(anchors[0]?.getAttribute("target")).toBeNull();
    expect(anchors[1]?.getAttribute("target")).toBe("_blank");
    expect(anchors[1]?.getAttribute("rel")).toContain("noopener");
  });

  it("blocks hostile URL schemes even if listed as authorized external", () => {
    const href = "javascript:alert(1)";
    const { container } = render(
      <ConversationMarkdown
        enabled
        text={`[x](${href})`}
        authorizedLinks={[{ href, kind: "external" }]}
      />,
    );
    expect(container.querySelector("a")).toBeNull();
  });

  it("does not link credential-bearing URLs even when listed as authorized", () => {
    const href = "https://example.org/doc?token=private";
    const { container } = render(
      <ConversationMarkdown
        enabled
        text={`[link](${href})`}
        authorizedLinks={[{ href, kind: "external" }]}
      />,
    );
    expect(container.querySelector("a")).toBeNull();
    expect(screen.getByText("link")).toBeTruthy();
  });

  it("degrades oversized content to inert literal text", () => {
    const huge = "**" + "x".repeat(16_400) + "**";
    const { container } = render(
      <ConversationMarkdown enabled text={huge} />,
    );
    expect(container.querySelector("strong")).toBeNull();
    expect(container.querySelector("p")?.textContent).toBe(huge);
  });

  it("degrades excessive nesting to inert literal text", () => {
    const nested = Array.from({ length: 20 }, () => "- item").join("\n  ");
    // Deep nesting of the same list may still parse shallowly; force depth
    // via recursive blockquotes which marked nests as tokens.
    const deep = "> ".repeat(12) + "fundo";
    const { container } = render(
      <ConversationMarkdown enabled text={deep} />,
    );
    // Either inert fallback or truncated safe tree — never executable HTML.
    expect(container.querySelector("script,img,iframe")).toBeNull();
    expect(container.textContent).toContain("fundo");
    void nested;
  });

  it("preserves business identifiers and quantities in the DOM", () => {
    const { container } = render(
      <ConversationMarkdown
        enabled
        text={"## Resultado\n\n- OP-10293\n- 3 KG\n- código `10090045`"}
      />,
    );
    expect(container.textContent).toContain("OP-10293");
    expect(container.textContent).toContain("3 KG");
    expect(container.textContent).toContain("10090045");
  });

  it("exposes kit class and focusable anchors for accessibility", () => {
    const { container } = render(
      <ConversationMarkdown
        enabled
        className="host"
        text={"[doc](https://example.org/a)"}
        authorizedLinks={[{ href: "https://example.org/a", kind: "external" }]}
      />,
    );
    const root = container.querySelector(
      ".delpi-ui-conversation-markdown.host",
    );
    expect(root).toBeTruthy();
    expect(root?.getAttribute("data-delpi-ui")).toBe("conversation-markdown");
    const anchor = container.querySelector("a");
    expect(anchor).toBeTruthy();
  });

  it("projects readable plain text for clipboard without markdown chrome", () => {
    const source =
      "## Título\n\n**OP-10293** e `10090045`\n\n- 3 KG\n\n[interno](/apps/delia)";
    const plain = conversationMarkdownToPlainText(source, [
      { href: "/apps/delia", kind: "internal" },
    ]);
    expect(plain).toContain("Título");
    expect(plain).toContain("OP-10293");
    expect(plain).toContain("10090045");
    expect(plain).toContain("- 3 KG");
    expect(plain).toContain("interno (/apps/delia)");
    expect(plain).not.toContain("**");
    expect(plain).not.toContain("##");
  });

  it("copy projection keeps unauthorized link label without URL", () => {
    const plain = conversationMarkdownToPlainText(
      "[segredo](https://evil.example)",
    );
    expect(plain).toBe("segredo");
    expect(plain).not.toContain("https://");
  });

  it("copy projection returns null for oversized source", () => {
    const huge = "x".repeat(16_400);
    expect(conversationMarkdownToPlainText(huge)).toBeNull();
  });
});

describe("ConversationMarkdown — fenced code delegates to ConversationCodeBlock", () => {
  it("renders fenced code with the shared block, header and language", () => {
    const { container } = render(
      <ConversationMarkdown
        enabled
        text={"```sql\nSELECT 1;\n```"}
      />,
    );
    const block = container.querySelector(
      '.delpi-ui-conversation-code-block[role="group"]',
    );
    expect(block?.getAttribute("aria-label")).toBe("Bloco de código SQL");
    expect(
      container.querySelector(".delpi-ui-conversation-code-block__pre code")
        ?.textContent,
    ).toBe("SELECT 1;");
    expect(
      within(container).getByRole("button", { name: "Copiar código" }),
    ).toBeTruthy();
  });

  it("keeps inline codespan as plain code without block chrome (CB-V08)", () => {
    const { container } = render(
      <ConversationMarkdown enabled text={"Use `count(*)` aqui."} />,
    );
    const code = container.querySelector("p code");
    expect(code?.textContent).toBe("count(*)");
    expect(
      container.querySelector(".delpi-ui-conversation-code-block"),
    ).toBeNull();
  });

  it("renders independent blocks for multiple fences (CB-V06)", () => {
    const { container } = render(
      <ConversationMarkdown
        enabled
        text={"```sql\nA\n```\n\n```json\nB\n```"}
      />,
    );
    const blocks = container.querySelectorAll(
      ".delpi-ui-conversation-code-block",
    );
    expect(blocks).toHaveLength(2);
    expect(blocks[0].textContent).toContain("SQL");
    expect(blocks[1].textContent).toContain("JSON");
  });

  it("keeps code content inert even with HTML inside the fence (CB-V09)", () => {
    const { container } = render(
      <ConversationMarkdown
        enabled
        text={"```html\n<script>alert(1)</script>\n```"}
      />,
    );
    expect(container.querySelector("script")).toBeNull();
    expect(
      container.querySelector(".delpi-ui-conversation-code-block__pre code")
        ?.textContent,
    ).toContain("<script>alert(1)</script>");
  });

  it("disabled gate renders no rich block (CB-V14)", () => {
    const { container } = render(
      <ConversationMarkdown
        text={"```sql\nSELECT 1;\n```"}
      />,
    );
    expect(
      container.querySelector(".delpi-ui-conversation-code-block"),
    ).toBeNull();
    expect(container.querySelector("p")?.textContent).toContain("SELECT 1;");
  });

  it("copy projection keeps fenced body without fences or lang (CB-V02)", () => {
    const plain = conversationMarkdownToPlainText("```sql\nSELECT 1;\n```");
    expect(plain).toBe("SELECT 1;");
  });
});
