/**
 * PROPOSAL PROBE — marked.lexer facts for the future ConversationMarkdown.
 *
 * DELIA-UX-CONVERSATION-MARKDOWN-B2-G1-G2-R2 / doc 84 §5.1/§5.3.
 *
 * Asserts the token stream behaviour of `marked.lexer` (REUSE decision)
 * under adversarial input: every unsafe construct arrives as a discrete
 * token TYPE, so a deny-by-construction token→React renderer can drop or
 * downgrade it before materializing any element. This probes the PARSER
 * and the PROPOSED link policy — it does not prove a renderer that does
 * not exist yet.
 */
import { describe, expect, it } from "vitest";
import { marked } from "marked";

type Flat = { type: string; depth: number; href?: string };

function flatten(src: string): Flat[] {
  const out: Flat[] = [];
  const walk = (t: { type: string; href?: string; tokens?: unknown[]; items?: unknown[] }, d: number) => {
    out.push({ type: t.type, depth: d, href: t.href });
    for (const c of (t.tokens ?? t.items ?? []) as { type: string; href?: string }[]) {
      if (typeof c === "object") walk(c, d + 1);
    }
  };
  marked.lexer(src).forEach((t) => walk(t as never, 0));
  return out;
}

function types(src: string): string[] {
  return flatten(src).map((t) => t.type);
}

function linkHrefs(src: string): string[] {
  return flatten(src)
    .filter((t) => t.type === "link")
    .map((t) => t.href ?? "");
}

/**
 * Proposed href policy (doc 84 §2.4 / L1 decision): only internal
 * absolute `/` paths and verified `https:` destinations may navigate.
 * Emission additionally requires a typed governed source — the policy
 * below is the CONSUMER-side deny rule; producer emission stays
 * fail-closed while `LINK_L1_CAPABILITY_BINDINGS=TO_INVENTORY`.
 */
function hrefAllowed(href: string): boolean {
  if (href.startsWith("/")) {
    return !href.startsWith("//") && !/[/\\][.]/.test(href);
  }
  return /^https:\/\/[\w.-]+/.test(href);
}

describe("marked.lexer — discrete unsafe token types (probe)", () => {
  it("emits html tokens for inline and block HTML — never executes", () => {
    const t = types("<b>x</b> <script>alert(1)</script> texto\n\n<iframe src=x></iframe>");
    expect(t).toContain("html");
    expect(t).not.toContain("script");
  });

  it("emits image token — renderer must drop it (no remote fetch)", () => {
    expect(types("texto ![alt](https://evil.example/x.png)")).toContain("image");
  });

  it("emits GFM table token — out of the conversational allowlist", () => {
    expect(types("| a | b |\n|---|---|\n| 1 | 2 |")).toContain("table");
  });

  it("emits code token for mermaid fence — renders as inert code", () => {
    const t = flatten("```mermaid\ngraph TD; A-->B\n```");
    expect(t[0].type).toBe("code");
    expect(types("```mermaid\ngraph TD; A-->B\n```")).not.toContain("html");
  });

  it("emits checkbox tokens inside list items — render as literal text", () => {
    expect(types("- [ ] task\n- [x] done")).toContain("checkbox");
  });

  it("does not cap nesting — renderer must enforce depth/node limits", () => {
    const t = flatten("- a\n  - b\n    - c\n      - d\n        - e\n          - f");
    expect(Math.max(...t.map((x) => x.depth))).toBeGreaterThanOrEqual(10);
  });

  it("emits del token for strikethrough", () => {
    expect(types("~~riscado~~")).toContain("del");
  });

  it("emits autolink for bare https URL — link policy still applies", () => {
    expect(linkHrefs("veja https://vendor.example/x")).toEqual([
      "https://vendor.example/x",
    ]);
  });
});

describe("marked.lexer — link token hrefs arrive raw; policy decides (probe)", () => {
  it.each([
    "javascript:alert(1)",
    "data:text/html;base64,PHNjcmlwdD4=",
    "blob:https://evil.example/x",
    "attachment:pending:uuid",
    "JaVaScRiPt:alert(1)",
    "java%73cript:alert(1)",
    "../sibling",
    "./local",
    "#anchor",
    "//evil.example/x",
    "mailto:a@b.example",
    "http://insecure.example/x",
    "file:///etc/passwd",
  ])("rejects %s", (href) => {
    expect(linkHrefs(`[clique](${href})`)).toEqual([href]);
    expect(hrefAllowed(href)).toBe(false);
  });

  it.each(["/apps/my-requests", "/profile", "/apps/delia"])(
    "accepts internal same-origin path %s",
    (href) => {
      expect(hrefAllowed(href)).toBe(true);
    },
  );

  it.each([
    "https://vendor.example/doc",
    "https://docs.delivery.local/x",
  ])("accepts verified https destination %s", (href) => {
    expect(hrefAllowed(href)).toBe(true);
  });
});
