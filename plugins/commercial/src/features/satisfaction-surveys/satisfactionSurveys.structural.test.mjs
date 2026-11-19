import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const sources = readdirSync(here)
  .filter((name) => /\.tsx?$/.test(name) && !name.endsWith(".test.ts"))
  .map((name) => ({ name, text: readFileSync(join(here, name), "utf8") }));
const api = readFileSync(join(here, "../../api/satisfactionSurveysApi.ts"), "utf8");
const css = readFileSync(join(here, "../../styles/satisfaction.css"), "utf8");
const listPage = sources.find((s) => s.name === "SatisfactionSurveysPage.tsx")?.text ?? "";
const content = readFileSync(
  join(here, "../../content/satisfactionSurveysContent.ts"),
  "utf8",
);

describe("Pesquisa de Satisfação (A/B) — guardrails estruturais", () => {
  it("MFE só fala com a commercial-api (sem api-delpi)", () => {
    assert.match(api, /commercialApiUrl/);
    assert.doesNotMatch(api, /api-delpi|apiDelpiUrl|API_DELPI/);
    for (const { name, text } of sources) {
      assert.doesNotMatch(text, /api-delpi|apiDelpiUrl|API_DELPI/, name);
    }
  });

  it("não persiste dados da pesquisa no navegador", () => {
    for (const { name, text } of sources) {
      assert.doesNotMatch(text, /localStorage|sessionStorage|document\.cookie/, name);
    }
  });

  it("prévia de e-mail usa somente HTML escapado por buildInviteHtml", () => {
    const preview = sources.find((s) => s.name === "InvitePreview.tsx")?.text ?? "";
    assert.match(preview, /buildInviteHtml/);
    assert.doesNotMatch(preview, /dangerouslySetInnerHTML/);
    for (const { name, text } of sources.filter((s) => s.name.endsWith(".tsx"))) {
      assert.doesNotMatch(text, /dangerouslySetInnerHTML/, name);
    }
  });

  it("CSS é só layout de página: sem seletor do kit", () => {
    assert.doesNotMatch(css, /\.delpi-ui-/);
    assert.doesNotMatch(css, /\.cm-(button|field|dialog|badge|card)\b/);
  });

  it("CSS não introduz cores literais (somente tokens/var)", () => {
    assert.doesNotMatch(css, /#[0-9a-fA-F]{3,8}\b/);
    assert.doesNotMatch(css, /\b(?:rgb|rgba|hsl|hsla)\(/i);
  });

  it("não implementa resultados nesta fatia (asserção alinhada à especificação vigente UI-02 §3.1 + Q24)", () => {
    for (const { name, text } of sources) {
      assert.doesNotMatch(text, /Ver resultados|Respostas por empresa/i, name);
      assert.doesNotMatch(
        text,
        /satisfaction-results|survey-results|respostas-por-empresa|results-path|buildResults/i,
        name,
      );
    }
  });
});

describe("Pesquisa de Satisfação — lista de campanhas (UI-02 P2)", () => {
  it("hero renderiza etiqueta MARKETING e o título da página, sem aviso de escopo parcial", () => {
    assert.match(listPage, /eyebrow=\{copy\.eyebrow\}/);
    assert.match(content, /eyebrow:\s*"MARKETING · PESQUISA DE SATISFAÇÃO"/);
    assert.match(listPage, /title=\{/);
    assert.match(listPage, /label=\{copy\.title\}/);
    assert.match(content, /title:\s*"Configuração das Pesquisas"/);
    assert.doesNotMatch(listPage, /partialScope/);
    assert.doesNotMatch(listPage, /Escopo parcial/);
  });

  it("«Atualizado em» usa aria-live, formato dd/mm/aaaa, hh:mm e «Atualizando…» na recarga", () => {
    assert.match(listPage, /aria-live="polite"/);
    assert.match(listPage, /formatSurveyUpdatedAt\(lastSuccessAt\)/);
    assert.match(listPage, /SATISFACTION_CONTENT\.updatedAt/);
    assert.match(listPage, /delpi-ui-section-hint-label/);
    // §5.5 item 4: o indicador «Atualizando…» é renderizado enquanto recarrega.
    assert.match(listPage, /refreshing/);
    assert.match(listPage, /SATISFACTION_CONTENT\.updating/);
    assert.match(content, /updating:\s*"Atualizando…"/);
  });

  it("preserva as três chaves de preferência da DataTableSection", () => {
    assert.match(listPage, /commercial:satisfaction-campaigns:layout/);
    assert.match(listPage, /commercial:satisfaction-campaigns:columns:v1/);
    assert.match(listPage, /commercial:satisfaction-campaigns:table-font-size:v1/);
    assert.match(listPage, /usePersistedViewLayout/);
    assert.match(listPage, /useTableColumnVisibility/);
    assert.match(listPage, /useTableFontSize/);
  });

  it("todas as colunas da tabela ordenam e dividem o estado com os cards", () => {
    const sortableCount = (listPage.match(/sortable:\s*true/g) ?? []).length;
    assert.equal(sortableCount, 5, "5 colunas sortable (Campanha/período + 4)");
    assert.match(listPage, /CommercialDataCardsSortBar/);
    assert.match(listPage, /sortKey=\{sort\.sortKey\}/);
    assert.match(listPage, /sortDirection=\{sort\.sortDirection\}/);
    assert.match(listPage, /onSortChange=\{handleSortChange\}/);
    assert.match(listPage, /value=\{sort\.sortKey \?\? "name"\}/);
    assert.match(listPage, /value=\{sort\.sortDirection\}/);
  });

  it("card usa título, selo, campo Período e os três números", () => {
    assert.match(listPage, /label:\s*copy\.cardPeriod/);
    assert.match(content, /cardPeriod:\s*"Período"/);
    assert.match(listPage, /valueTone:\s*"title"/);
    assert.match(listPage, /SatisfactionStatusBadge status=\{campaign\.status\}/);
    assert.match(listPage, /colResponded|colResponseRate|colParticipants/);
  });

  it("paginação cliente (20) com CommercialPagination e reset via useClientPagination", () => {
    assert.match(listPage, /useClientPagination\(sortedRows, pageSize\)/);
    assert.match(listPage, /CommercialPagination/);
    assert.match(listPage, /TABLE_PAGE_SIZE_OPTIONS/);
    assert.match(listPage, /DEFAULT_PAGE_SIZE = 20/);
  });
});
