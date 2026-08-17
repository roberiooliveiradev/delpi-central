#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const detail = readFileSync(join(here, "SellerPortfolioDetail.tsx"), "utf8");
const page = readFileSync(join(here, "SellerPortfolioDetailPage.tsx"), "utf8");

describe("SellerPortfolioDetail UX", () => {
  it("usa CustomerSearchPicker com avatares e vincular selecionados", () => {
    assert.match(detail, /CustomerSearchPicker/);
    assert.match(detail, /CustomerAvatar/);
    assert.match(detail, /useCustomerAvatarPresence/);
    assert.match(detail, /onAddCustomers/);
    assert.match(detail, /Vincular selecionados/);
    assert.match(detail, /maxSelected=\{20\}/);
    assert.doesNotMatch(detail, /useActiveCustomerSearch/);
    assert.doesNotMatch(detail, /apiDelpiUrl|API_DELPI|\/apps\/api-delpi/);
  });

  it("page faz vínculo em lote sequencial", () => {
    assert.match(page, /handleAddCustomers/);
    assert.match(page, /linkingCustomers/);
    assert.match(page, /Vínculo parcial|vinculado\(s\)/);
  });

  it("permite desvincular clientes em lote com checkbox e toolbar", () => {
    assert.match(detail, /NativeCheckboxControl/);
    assert.match(detail, /selectedLinkedKeys/);
    assert.match(detail, /Desvincular selecionados/);
    assert.match(detail, /onRemoveCustomers/);
    assert.match(detail, /CommercialDataListToolbar/);
    assert.match(page, /handleRemoveCustomers/);
    assert.match(page, /unlinkingCustomers/);
    assert.match(page, /Desvínculo parcial|removido\(s\)/);
  });

  it("adiciona usuários em lote com avatares no picker e na tabela", () => {
    assert.match(detail, /TaskUserChipAvatar/);
    assert.match(detail, /maxSelected=\{10\}/);
    assert.match(detail, /Adicionar selecionados/);
    assert.match(detail, /onAddMembers/);
    assert.match(detail, /searchMemberCandidates/);
    assert.doesNotMatch(detail, /onAddMember\(/);
    assert.match(page, /handleAddMembers/);
    assert.match(page, /addingMembers/);
    assert.match(page, /Inclusão parcial|adicionado\(s\)/);
  });

  it("concentra infos e edição de nome no PageHero", () => {
    assert.match(page, /CommercialPageHero/);
    assert.match(page, /Editar nome/);
    assert.match(page, /editingName/);
    assert.match(page, /highlights/);
    assert.doesNotMatch(detail, /Nome de exibição/);
    assert.doesNotMatch(detail, /onSaveName|onDeactivate|onTransfer/);
  });

  it("oferece atalhos de seleção filtrada nos vinculados", () => {
    assert.match(detail, /linkedFilter/);
    assert.match(detail, /filteredLinked/);
    assert.match(detail, /Selecionar todos filtrados/);
    assert.match(detail, /Limpar seleção/);
    assert.match(detail, /excludeKeys=\{linkedKeys\}/);
  });

  it("colapsa busca de clientes e usuários quando já há vinculados", () => {
    assert.match(detail, /memberSearchOpen|setMemberSearchOpen/);
    assert.match(detail, /customerSearchOpen|setCustomerSearchOpen/);
    assert.match(detail, /PORTFOLIO_MEMBERS_CONTENT\.addMoreMembers/);
    assert.match(detail, /PORTFOLIO_CUSTOMERS_CONTENT\.addMoreCustomers/);
    assert.match(detail, /showMemberSearch/);
    assert.match(detail, /showCustomerSearch/);
    const content = readFileSync(
      join(here, "../../content/portfolioMembersContent.ts"),
      "utf8",
    );
    assert.match(content, /addMoreMembers/);
    assert.match(content, /addMoreCustomers/);
  });
});
