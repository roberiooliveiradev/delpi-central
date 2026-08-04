import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/**
 * Embedded chat (TV Copiloto): coluna única, sem sidebar do shell completo.
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

  it("ChatPage em embedded não navega URL ao ativar sessão", () => {
    expect(page).toMatch(/if \(isEmbedded\) return;/);
    expect(page).toMatch(/onSessionActivated/);
  });

  it("CSS esconde mdc-chat-sidebar (não seletor legado layout__sidebar)", () => {
    expect(css).toMatch(/\.mdc-embedded-chat \.mdc-chat-sidebar/);
    expect(css).not.toMatch(/mdc-chat-layout__sidebar/);
    expect(css).toMatch(/grid-template-columns:\s*minmax\(0,\s*1fr\)/);
  });

  it("shell embedded força coluna única no layout", () => {
    expect(layout).toMatch(/\.mdc-chat-shell--embedded/);
    expect(page).toMatch(/variant\?\: \"full\" \| \"embedded\"/);
    expect(page).toMatch(/isEmbedded \? null : \(/);
  });
});
