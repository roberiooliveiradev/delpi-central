#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const src = join(dirname(fileURLToPath(import.meta.url)), "../..");

function readSrc(relative) {
  return readFileSync(join(src, relative), "utf8");
}

describe("user manual page", () => {
  it("conteúdo e página exportam o manual", () => {
    const content = readSrc("content/userManualContent.ts");
    assert.match(content, /export const USER_MANUAL_CONTENT/);
    assert.match(content, /pageTitle: \"Manual do usuário\"/);
    assert.match(content, /USER_MANUAL_TERM_CATALOG/);
    assert.match(content, /Catálogo de termos/);
    assert.match(content, /Minha Carteira → ABC/);
    assert.match(content, /painel ABC/);
    assert.match(content, /Administração → SLAs/);
    assert.match(content, /Onde configuro os SLAs/);
    assert.match(content, /Centro do cliente é o nome da WEG/);
    assert.match(content, /não altera funil|não muda o funil|Funil, novos negócios e metas/);
    assert.match(content, /O que é código, loja e centro/);
    assert.match(content, /Por que vejo duas linhas do mesmo cliente/);
    assert.match(content, /qualquer cliente com centros na SA7/);
    assert.match(content, /Separar unidades do mesmo cliente/);
    assert.match(content, /O centro aparece no link da Conta/);
    assert.match(content, /Onde vejo o centro em Meus pedidos/);
    assert.match(content, /Posso ordenar a carteira pelo centro/);
    assert.match(content, /Como vinculo um centro novo na carteira/);
    assert.match(content, /Filtrar pedidos por centro do cliente/);
    assert.match(content, /Quatro conceitos/);
    assert.match(content, /Onde vejo o ROL do mês/);
    assert.match(content, /busca de caminhos.*indicadores/);
    assert.match(content, /popover ancorado à barra/);
    assert.match(content, /Barra superior → Buscar/);
    assert.match(content, /Indicadores do período/);
    assert.match(content, /busca de caminhos também acha Visão geral/);
    assert.match(content, /No consolidado \(unidade Todas\) a Visão geral mostra meta/);
    assert.match(
      content,
      /agregam Santa Catarina \+ Espírito Santo pelo método|agregação SC\+ES pelo SI/,
    );
    assert.match(content, /Como vejo o histórico em quantidade/);
    assert.match(content, /use Séries para escolher a série/);
    assert.match(content, /Ponderar período parcial|exclui o bucket incompleto/);
    assert.match(content, /Milheiro \| Peças|1 MI = 1000 PC/);
    assert.match(content, /data de colocação do pedido|Backlog CRM|ficam para o CRM/);
    const catalog = readSrc("content/userManualTermCatalog.ts");
    assert.match(catalog, /export const USER_MANUAL_TERM_CATALOG/);
    assert.match(catalog, /term: \"EXW\"/);
    assert.match(catalog, /term: \"FOB\"/);
    assert.match(catalog, /term: \"CIF\"/);
    assert.match(catalog, /applies:/);
    assert.match(catalog, /Minha Carteira → ABC/);
    assert.match(catalog, /agregação SC\+ES pelo SI/);
    assert.match(catalog, /Métrica R\$ \/ Qtd \/ Ambos/);
    assert.match(catalog, /Milheiro \/ Peças/);
    const page = readSrc("features/help/UserManualPage.tsx");
    assert.match(page, /USER_MANUAL_CONTENT/);
    assert.match(page, /glossaryGroups/);
    assert.match(page, /Onde aparece/);
    assert.match(page, /UserManualLinkedText/);
    assert.match(page, /CommercialUserManual/);
    const links = readSrc("content/userManualToolLinks.ts");
    assert.match(links, /MANUAL_TOOL_TARGETS/);
    assert.match(links, /splitManualTextWithToolLinks/);
    assert.match(links, /Minha Carteira → ABC/);
    assert.match(links, /\?panel=abc/);
    assert.match(links, /Administração → SLAs/);
    assert.match(links, /administration_slas/);
  });

  it("App e manifesto expõem /help", () => {
    const app = readSrc("App.tsx");
    assert.match(app, /UserManualPage/);
    assert.match(app, /view === \"help\"/);
    const routes = readSrc("app/pluginRoutes.ts");
    assert.match(routes, /relativePath === \"help\"/);
    assert.match(routes, /help: \"help\"/);
    const manifest = readFileSync(
      join(src, "..", "commercial.manifest.json"),
      "utf8",
    );
    assert.match(manifest, /\/apps\/commercial\/help/);
  });
});
