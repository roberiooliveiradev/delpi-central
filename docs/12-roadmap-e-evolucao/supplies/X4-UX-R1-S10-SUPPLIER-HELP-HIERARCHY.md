# X4.UX-R1.S10 — Supplier Form Contextual Help Hierarchy

**Data:** 2026-10-23 · **Status:** `ACCEPT_WITH_RESIDUAL`
**Owner:** `plugins/supplies` (MFE-only — zero backend)
**Escopo autorizado:** apresentação e textos de ajuda dos formulários de criação/edição de fornecedores. Sem contratos, regras, RBAC, integrações ou persistência.

---

## 1. Problema original (evidência PO)

- Help de **Contato** e **Compras** exibiam o mesmo texto genérico de todo o cadastro (`suppliersCreateFields` — "Todos os campos do contrato de cadastro, organizados por seção…"), repetido nas cinco seções de `SupplierCreatePage`.
- Repetição de orientações sobre CNPJ, catálogos, CEP, obrigatoriedade e revisão final.
- Ausência de descrição funcional própria por seção.
- Residual E7.V1: complemento de tamanho `Até XX caracteres, conforme o contrato de integração com o ERP.` (jargão técnico).

## 2. Causa-raiz

`SupplierCreatePage` passava `hint={SP_HELP.suppliersCreateFields}` para **todos** os `SuppliesSectionCard`; em `SupplierDetailPage` apenas a seção identificação tinha hint próprio. O conteúdo era genérico por construção — o componente `HelpTooltip` estava correto (confirmado: não era problema do design system).

## 3. Hierarquia implementada

| Nível | Onde | Conteúdo |
|---|---|---|
| **Hero** | `C.createDescription` (criação) / `C.editHint` (edição) | Objetivo da página, formas de iniciar, revisão, disponibilidade de gravação — nunca promete escrita habilitada |
| **Seção** | `subtitle` do `SuppliesSectionCard` (visível, sem hover) | `supplierSectionDescriptions` — fonte única em `content.ts`, 5 descrições funcionais distintas |
| **Campo** | `spec.help` (registry, inalterado) | Explicação funcional + `(TOTVS: SA2.A2_*)` — padrão E7 preservado |

### Textos finais (aprovados pelo spec)

- **Hero criação:** "Preencha as informações cadastrais do fornecedor. Você pode consultar dados públicos pelo CNPJ ou informar os dados manualmente. Confira as informações e revise o cadastro antes de concluir. O envio ao Protheus estará disponível quando autorizado."
- **Hero edição:** "Atualize as informações cadastrais necessárias. Código, loja e documento fiscal são protegidos. Antes de concluir, revise os campos alterados. A gravação depende da disponibilidade e das autorizações do ambiente." (renderizado como nota sob o hero no modo edição; o slot `description` do hero preserva nome/código/loja do fornecedor.)
- **Seções:** 5 descrições conforme spec §6 — identificação, endereço (menção ao CEP sem prometer auto-aplicação), contato, fiscal (sem aconselhamento tributário), compras.

### Realocação do conteúdo genérico removido

| Conteúdo do texto antigo | Destino |
|---|---|
| Objetivo do cadastro / revisão / gravação | Hero (já presente em `createDescription`/`editHint`) |
| CEP e sugestões | Descrição da seção Endereço + help do campo `postal_code` |
| Catálogos por descrição | Helps dos campos com catálogo (E7) |
| Obrigatoriedade | Validações dos campos (inalteradas) |
| "código+loja identificador" | Help do campo + meta da ficha |

Chaves removidas: `suppliersCreateFields`, `suppliersIdentification` (sem consumidores após a mudança).

## 4. Correções de jargão

- `supplierFieldMaxLengthHint`: `Até X caracteres, conforme o contrato de integração com o ERP.` → **`Máximo de X caracteres.`** (residual E7.V1 fechado).
- `readonlyFieldHint`: `homologada no contrato do ERP` → `ainda não foi liberada no ERP`.
- `SUPPLIERS_CONTENT.titleHint` e `suppliersColTaxId`: `mascarados do backend` → `mascarados (proteção LGPD)` / `(LGPD)`.
- `userManualContent`: seção descreve que cada seção mostra sua finalidade abaixo do título.

## 5. Componentes reutilizados

- `SuppliesSectionCard` (`createDashboardSectionCard`, plugin-ui) — prop `subtitle` nativa, já renderiza descrição secundária visível sob `<h2>` semântico. Nenhum componente novo criado.
- `FieldLabel`/`HelpTooltip` — sem alterações (acessibilidade E7 confirmada).

## 6. Testes

- **+6 testes S10** em `suppliers.test.ts`: 5 descrições distintas/não-vazias; sem texto genérico antigo; cobertura create+edit na mesma fonte; heroes específicos sem promessa de escrita; sem jargão técnico (`DTO|BFF|serializer|contrato de integração`) em nenhum texto UX; hint de tamanho novo.
- **381 testes MFE passam** (43 arquivos) · `tsc -b` PASS · eslint escopado 0 erros (1 warning pré-existente `set-state-in-effect` em `SupplierDetailPage:103`, fora do escopo) · `vite build` PASS.
- Os 54 helps E7 e referências TOTVS seguem protegidos pelos testes E7 (PASS).

## 7. Segurança / escopo

Zero diff fora de `plugins/supplies` + docs. Sem contrato, RBAC, permissão, integração, persistência ou feature gate alterados. Validações de campos inalteradas.

## 8. Residuais

- `E10_VISUAL = INCONCLUSIVE` — sem navegador autenticado; smoke de bundle confirma textos publicados.
- Responsividade/temas/teclado: garantidos por componentes canônicos (subtitle com quebra natural; tooltip com clamp+Escape+foco) — verificação visual pendente.
- Handoffs E7 pendentes (`A2_CLIENTE`, `tax-groups`, `risk-codes`).

## 9. Próxima etapa

Aceite visual autenticado do novo hierarquia (hero + subtítulos visíveis nas 5 seções de ambas as telas).


## 10. Revisão GPT — S10 (2026-10-23)

**Decisão: `ACCEPT_WITH_RESIDUAL` para implementação S10 em código.** Inspeção em GitHub no source `bf3db64c8e` confirmou `supplierSectionDescriptions` como fonte compartilhada, `subtitle` aplicado em `SupplierCreatePage` e `SupplierDetailPage`, descrições de hero distintas e complemento de limite simplificado. As 54 ajudas E7 continuam no registry segundo a evidência do executor e testes estruturais. Nenhuma mudança de backend/RBAC/integração consta do relatório.

**Classificação da evidência:** MFE 381 PASS, typecheck, lint, build, deploy MFE-only e bundle `App-BWLqb0qi.js` = **reportados pelo Cursor**, não reexecutados pelo GPT. `S10_VISUAL = INCONCLUSIVE`; os componentes reutilizados não substituem prova de desktop/mobile, claro/escuro, teclado e leitura efetiva. O rótulo `E10_VISUAL` usado no relatório S10 é ambíguo em relação à feature E10/WF-15 histórica: usar **`S10_VISUAL`** em relatórios futuros para não confundir gates.

**Aceite pendente:** validar com navegador autenticado se os subtítulos das cinco seções são visíveis sem hover na criação e edição, se o texto genérico antigo desapareceu, se tooltips dos campos continuam acessíveis e sem clipping, e se não existe promessa de gravação enquanto gates ERP estiverem OFF. Nenhuma escrita real no Protheus autorizada por esta revisão.
