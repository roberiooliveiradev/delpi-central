import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

function read(name: string): string {
  return readFileSync(join(dir, name), "utf8");
}

describe("SupplierIntegrationStatusCard (X4.REST-STATUS.S1/S2) — boundaries", () => {
  it("fala somente com supplies-api via httpClient canônico", () => {
    const api = read("api.ts");
    expect(api).toContain('from "../../api/httpClient"');
    expect(api).toContain('"/suppliers/integration-status"');
    const card = read("SupplierIntegrationStatusCard.tsx");
    for (const text of [api, card]) {
      expect(text).not.toMatch(/api-delpi|apiDelpi/);
      expect(text).not.toMatch(/Service-Authorization|s2s/i);
      expect(text).not.toMatch(/192\.168|8061|8701|restall/i);
    }
  });

  it("diagnóstico é estritamente read-only — sem escrita ERP", () => {
    const api = read("api.ts");
    const statusFn = api.slice(api.indexOf("getSuppliersIntegrationStatus"));
    expect(statusFn).toContain("httpGet");
    expect(statusFn).not.toMatch(/httpPost|httpPut|httpDelete|httpPatch/);
  });

  it("card compartilhado montado nas duas páginas sob capabilities.manage", () => {
    for (const page of ["SuppliersPage.tsx", "SupplierDetailPage.tsx"]) {
      const text = read(page);
      expect(text).toContain("SupplierIntegrationStatusCard");
      expect(text).toContain("session.capabilities.manage");
      expect(text).toContain("useSuppliesSession");
    }
  });

  it("refresh manual sem polling nem requisições concorrentes", () => {
    const card = read("SupplierIntegrationStatusCard.tsx");
    expect(card).not.toMatch(/setInterval|setTimeout/);
    expect(card).toContain("AbortController");
    expect(card).toContain("requestRef");
    expect(card).toMatch(/if \(checking\) return/);
    expect(card).toContain("disabled={checking}");
  });

  it("POST/PUT habilitado nunca é apresentado como gravação comprovada", () => {
    const card = read("SupplierIntegrationStatusCard.tsx");
    const content = read("content.ts");
    expect(card).toContain("statusStateNotTested");
    expect(card).toContain("statusWriteNotProvenNote");
    expect(content).not.toMatch(/gravação comprovada|POST validado|PUT validado/i);
    expect(card).not.toMatch(/post_validated|put_validated|write_proven/i);
  });

  it("estados confiáveis com timestamp e acessibilidade", () => {
    const card = read("SupplierIntegrationStatusCard.tsx");
    expect(card).toContain("aria-live");
    expect(card).toContain("aria-expanded");
    expect(card).toContain('role="alert"');
    expect(card).toContain("formatCheckedAt");
    expect(card).toContain("overallBadge");
    expect(card).toContain("authentication_http_status");
  });

  it("diferencia dependência upstream de indisponibilidade geral", () => {
    const card = read("SupplierIntegrationStatusCard.tsx");
    expect(card).toContain('"upstream_pending"');
    expect(card).toContain('"ready_for_attempt"');
    expect(card).toContain('"unavailable"');
    // nunca exibe "pronta" quando overall não for ready_for_attempt
    expect(card).not.toMatch(/overall.*===.*"ok"/);
  });

  it("nota de independência SQL preservada na expansão", () => {
    const card = read("SupplierIntegrationStatusCard.tsx");
    expect(card).toContain("statusSqlIndependentNote");
  });

  it("S2 — máquina de estados única closed/collapsed/expanded", () => {
    const card = read("SupplierIntegrationStatusCard.tsx");
    expect(card).toMatch(/"closed" \| "collapsed" \| "expanded"/);
    // collapsed→expanded, expanded→collapsed, *→closed, closed→collapsed
    expect(card).toContain('setView("collapsed")');
    expect(card).toContain('setView("closed")');
    expect(card).toContain('setView(expanded ? "collapsed" : "expanded")');
    // estado inicial recolhido
    expect(card).toMatch(/lastView[^=]*=\s*"collapsed"/);
    // reabrir sempre volta para collapsed
    expect(card).toMatch(/onClick=\{\(\) => setView\("collapsed"\)\}/);
  });

  it("S2 — flutuante no canto inferior direito, abaixo de modais do kit", () => {
    const css = readFileSync(join(dir, "../../index.css"), "utf8");
    const open = css.indexOf(".sp-suppliers-status-card {");
    const card = css.slice(open, css.indexOf("}", open));
    expect(card).toContain("position: fixed");
    expect(card).toContain("bottom:");
    expect(card).toContain("right:");
    // z-index baixo — modais/overlays oficiais usam 1200
    expect(card).toMatch(/z-index: 3[0-9]\b/);
    expect(card).not.toMatch(/z-index: (?:[4-9][0-9]|[0-9]{3,})/);
    expect(card).toContain("env(safe-area-inset-bottom");
  });

  it("S2 — fechar/reabrir preserva resultado sem nova chamada REST", () => {
    const card = read("SupplierIntegrationStatusCard.tsx");
    // cache de módulo compartilha estado entre lista e ficha sem refetch
    expect(card).toContain("lastStatus");
    expect(card).toContain("lastView");
    // transições de view nunca chamam runCheck/getSuppliersIntegrationStatus
    const viewFns = card
      .split("onClick")
      .filter((chunk) => chunk.includes('setView("'))
      .join("\n");
    expect(viewFns).not.toContain("runCheck");
    expect(viewFns).not.toContain("getSuppliersIntegrationStatus");
    // a única chamada REST continua sendo a ação manual explícita
    expect(card.match(/getSuppliersIntegrationStatus\(/g)).toHaveLength(1);
  });

  it("S2 — acionador discreto de reabertura com tooltip e ícone do kit", () => {
    const card = read("SupplierIntegrationStatusCard.tsx");
    const content = read("content.ts");
    expect(card).toContain("sp-suppliers-status-card__reopen");
    expect(card).toContain("statusReopenTooltip");
    expect(card).toContain("statusCloseAction");
    expect(content).toContain("Abrir diagnóstico da integração Protheus");
    expect(card).toContain('from "lucide-react"');
  });

  it("S2.R1 — widget montado via portal no body, fora do transform do host", () => {
    const card = read("SupplierIntegrationStatusCard.tsx");
    // âncora real na viewport: o host anima a rota com transform (fill both),
    // que captura position:fixed — o portal no body remove o containing block.
    expect(card).toContain('from "react-dom"');
    expect(card).toContain("createPortal(");
    expect(card).toContain("document.body");
    // wrapper do portal reaplica o escopo de tokens/seletores do MFE
    expect(card).toContain("dashboard-supplies-portal");
    expect(card).toContain("sp-suppliers-status-card-portal");
  });

  it("S2.R1 — painel expandido nunca ultrapassa o topo da viewport", () => {
    const css = readFileSync(join(dir, "../../index.css"), "utf8");
    const open = css.indexOf(".sp-suppliers-status-card__details {");
    const details = css.slice(open, css.indexOf("}", open));
    // altura limitada pela viewport real menos o cabeçalho/ações
    expect(details).toMatch(/calc\(100dvh - 1[0-9]{2}px\)/);
    expect(details).toContain("overflow-y: auto");
    expect(details).toContain("max-height");
  });

  it("S2 — acessibilidade: aria-expanded, Escape, foco devolvido ao acionador", () => {
    const card = read("SupplierIntegrationStatusCard.tsx");
    expect(card).toContain("aria-expanded");
    expect(card).toContain("aria-controls");
    expect(card).toContain("aria-label");
    expect(card).toContain('event.key === "Escape"');
    // Escape só recolhe quando expandido
    expect(card).toMatch(/Escape" && expanded/);
    // fechar nunca deixa foco em elemento oculto — devolve ao acionador
    expect(card).toContain("reopenRef.current?.focus()");
    // botões reais (não divs clicáveis)
    expect(card).toMatch(/<button[\s\S]*?type="button"/);
    const css = readFileSync(join(dir, "../../index.css"), "utf8");
    expect(css).toContain("prefers-reduced-motion");
  });
});
