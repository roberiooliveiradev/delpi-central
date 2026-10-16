import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ConversationMarkdown } from "./ConversationMarkdown";

describe("ConversationMarkdown — governed, disabled by default", () => {
  it("renders v1 content verbatim, with the same p/class node", () => {
    const source = "**OP-10293**\n<script>alert(1)</script> [abrir](https://example.org)";
    const { container } = render(<ConversationMarkdown className="delia-turn__content" text={source} />);
    const paragraph = container.querySelector("p.delia-turn__content");
    expect(paragraph?.textContent).toBe(source);
    expect(container.querySelector("a,strong,script,img")).toBeNull();
  });

  it("renders admitted textual Markdown semantically when explicitly enabled", () => {
    const { container } = render(<ConversationMarkdown enabled text={"## Resultado\n\n- OP-10293\n- 3 KG\n\n**Atenção** e `codigo`"} />);
    expect(container.querySelector("h4")?.textContent).toBe("Resultado");
    expect(container.querySelectorAll("li")).toHaveLength(2);
    expect(container.querySelector("strong")?.textContent).toBe("Atenção");
    expect(container.querySelector("code")?.textContent).toBe("codigo");
  });

  it("does not materialize HTML, images, tables or executable code", () => {
    const { container } = render(<ConversationMarkdown enabled text={'<script>window.evil=1</script>\n\n![remote](https://example.org/image.png)\n\n```mermaid\ngraph TD\n```'} />);
    expect(container.querySelector("script,img,iframe,svg,table")).toBeNull();
    expect(container.querySelector("pre code")?.textContent).toContain("graph TD");
  });

  it("does not create navigable links without an authorized destination", () => {
    const { container } = render(<ConversationMarkdown enabled text={"[interno](/apps/delia) [externo](https://example.org) [malicioso](javascript:alert(1))"} />);
    expect(container.querySelector("a")).toBeNull();
  });

  it("only renders explicitly authorized https and internal links", () => {
    const { container } = render(
      <ConversationMarkdown
        enabled
        text={"[interno](/apps/delia) [externo](https://example.org/doc) [outro](https://other.invalid)"}
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

  it("does not link credential-bearing URLs even when listed as authorized", () => {
    const href = "https://example.org/doc?token=private";
    const { container } = render(<ConversationMarkdown enabled text={`[link](${href})`} authorizedLinks={[{href,kind:"external"}]} />);
    expect(container.querySelector("a")).toBeNull();
    expect(screen.getByText("link")).toBeTruthy();
  });

  it("degrades oversized content to inert literal text", () => {
    const huge = "**" + "x".repeat(16_400) + "**";
    const { container } = render(<ConversationMarkdown enabled text={huge} />);
    expect(container.querySelector("strong")).toBeNull();
    expect(container.querySelector("p")?.textContent).toBe(huge);
  });
});
