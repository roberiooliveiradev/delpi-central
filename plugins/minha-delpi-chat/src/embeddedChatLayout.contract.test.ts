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

  it("troca de conversa não depende da URL do host", () => {
    const list = readFileSync(
      join(here, "ui/components/shell/ChatSidebarSessionList.tsx"),
      "utf8",
    );
    const projects = readFileSync(
      join(here, "ui/components/shell/ChatSidebarProjectsSection.tsx"),
      "utf8",
    );
    const item = readFileSync(
      join(here, "ui/components/shell/ChatConversationListItem.tsx"),
      "utf8",
    );

    expect(list).toMatch(/onClick=\{\(\) => onSelectSession\(session\)\}/);
    expect(list).not.toMatch(/onSelectSession: _onSelectSession/);
    expect(projects).toMatch(/onSelectSession\(session\)/);
    expect(projects).not.toMatch(/onSelectSession: _onSelectSession/);
    // Clique esquerdo com handler explícito não cai no fluxo só-URL.
    expect(item).toMatch(/if \(onClick\) \{[\s\S]*?event\.preventDefault\(\);/);
    expect(item).toMatch(/shouldOpenChatLinkInNewTab/);
  });

  it("embed usa rota interna e não degrada telas do chat", () => {
    expect(page).toMatch(/const activePathname = isEmbedded \? embeddedPathname : pathname/);
    expect(page).toMatch(/parseChatRoute\(activePathname\)/);
    expect(page).toMatch(/pathname: activePathname/);
    // Agentes/projetos/ajuda deixam de ser bloqueados no embed.
    expect(page).not.toMatch(/isEmbedded && currentView !== "chat"/);
    expect(page).not.toMatch(/onOpenHelp=\{isEmbedded \? undefined/);
    expect(page).not.toMatch(/onManageAgents=\{isEmbedded \? undefined/);
  });

  it("sidebar em gaveta expõe fechar em vez do rail colapsável", () => {
    const brand = readFileSync(
      join(here, "ui/components/shell/ChatSidebarBrand.tsx"),
      "utf8",
    );
    const brandCss = readFileSync(
      join(here, "ui/components/shell/ChatSidebarBrand.css"),
      "utf8",
    );

    expect(page).toMatch(/isDrawer=\{isEmbedded \|\| !isDesktop\}/);
    expect(brand).toMatch(/isDrawer\?: boolean/);
    expect(brand).toMatch(/\{!isDrawer \? \(/);
    expect(brandCss).toMatch(
      /\.mdc-chat-sidebar__brand--drawer \.mdc-chat-sidebar__close-mobile/,
    );
  });
});
