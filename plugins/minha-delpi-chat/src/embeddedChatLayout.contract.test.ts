import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/**
 * Embedded chat (TV Copiloto): coluna única + ChatSidebar canônica em drawer.
 */
describe("mdc-embedded-chat layout contract", () => {
  const here = dirname(fileURLToPath(import.meta.url));
  const css = readFileSync(join(here, "index.css"), "utf8");
  const embedded = readFileSync(join(here, "EmbeddedChat.tsx"), "utf8");
  const page = readFileSync(join(here, "ui/pages/ChatPage.tsx"), "utf8");
  const layout = readFileSync(join(here, "ui/layout/chat-layout.css"), "utf8");

  it("EmbeddedChat monta ChatPage em variant embedded", () => {
    expect(embedded).toMatch(/variant=\"embedded\"/);
    expect(embedded).toMatch(/setChatNavigationHostMode\(\"embedded\"\)/);
  });

  it("ChatPage em embedded persiste sessão e usa ChatSidebar canônica", () => {
    expect(page).toMatch(/if \(isEmbedded\) \{/);
    expect(page).toMatch(/writeEmbeddedSessionId/);
    expect(page).toMatch(/onSessionActivated/);
    expect(page).toMatch(/<ChatSidebar/);
    expect(page).not.toMatch(/EmbeddedSessionBar/);
    expect(page).toMatch(/isEmbedded \|\| !isDesktop \? openMobileSidebar/);
    expect(page).toMatch(/isCollapsed=\{!isEmbedded && isDesktop && isSidebarCollapsed\}/);
  });

  it("CSS embedded: coluna única + drawer da sidebar (não esconde ChatSidebar)", () => {
    expect(css).toMatch(/\.mdc-embedded-chat \.mdc-chat-sidebar/);
    expect(css).toMatch(/\.mdc-embedded-chat \.mdc-chat-sidebar--drawer-open/);
    expect(css).not.toMatch(/mdc-chat-layout__sidebar/);
    expect(css).toMatch(/grid-template-columns:\s*minmax\(0,\s*1fr\)/);
    expect(css).not.toMatch(
      /\.mdc-embedded-chat \.mdc-chat-sidebar,\s*\.mdc-embedded-chat \.mdc-chat-sidebar-backdrop[\s\S]*?display:\s*none/m,
    );
  });

  it("CSS do embedded compacta composer dual-options por container", () => {
    expect(css).toMatch(/\.mdc-embedded-chat \.mdc-chat-input__box--with-dual-composer-options/);
    expect(css).toMatch(/grid-template-columns:\s*auto minmax\(0,\s*1fr\) minmax\(0,\s*1fr\)/);
  });

  it("shell embedded força coluna única no layout", () => {
    expect(layout).toMatch(/\.mdc-chat-shell--embedded/);
    expect(page).toMatch(/variant\?\: \"full\" \| \"embedded\"/);
    expect(page).toMatch(/mdc-chat-shell--embedded/);
  });
});
