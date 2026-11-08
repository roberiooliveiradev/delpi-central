# D13 — Edição direta, diff automático e operações SA5 (ADD / UPDATE / REMOVE)

**Decisão PO:** 2026-11-08. **Status:** `PO_APPROVED_UX_DIRECTION / IMPLEMENTATION_PENDING / P0_VERIFICATION_FIX_REQUIRED / PRODUCTION_DEPLOY_SUSPENDED`.  
**Owners:** Portal Engenharia (MFE e experiência), Engineering API (domínio/aplicação, auditoria, revisão/verificação), api-delpi (leituras oficiais TOTVS), Engenharia/integração (regra técnica e aceite).  
**Referências obrigatórias:** [Blueprint D12](./MFE-PRC-D12-ROUTES-API-DELPI-IMPLEMENTATION-BLUEPRINT.md), [REF-012](./MFE-PRC-REF-012-INDIVIDUAL-FIELDS-AND-SUPPLIER-LINK-OPERATIONS.md), [Wireframe V2 de fornecedores](./MFE-PRC-WIREFRAME-FORNECEDORES-V2-APPROVED.md), regras de `AGENTS.md`.

> **Esta especificação substitui a interação antiga de UPDATE com checkboxes de campos, edição em controles separados e “Alterar vínculos de fornecedores”.** A identificação de alteração passa a ser automática; **o backend continua autoridade do change set e da conclusão**. As versões anteriores permanecem como histórico, não como instruções contraditórias.

## 1. O que se viu no DEV e por que alterar

A captura do PO mostra: (i) cada campo SB1 possui checkbox, valor `Atual no TOTVS`, e só então um **outro input** com justificativa; (ii) fornecedores usam checkbox geral `Alterar vínculos` e `Editar` abre controle adicional para PN/Catálogo; (iii) seleção de atributos por botões `+ PN`, `+ Catálogo`; (iv) a UI ainda usa textos de ajuda como `B1_LOCPAD — legado` pouco compreensíveis. Isso cria duas representações do mesmo campo, amplia altura e exige marcação manual.

**Target:** os valores SB1 e vínculos SA5 correntes são carregados por `edit-context`. O próprio campo visual já contém o valor oficial, editável. Usuário digita/seleciona outro valor, sistema calcula e destaca diffs automaticamente. Não há checkbox “alterar campo” nem edição paralela. A página não escreve ERP: gera **pedido técnico candidato**, sujeito a validação e read-back oficial após atuação manual no TOTVS.

## 2. Wireframe funcional — UPDATE direto

```text
ALTERAR PRODUTO [código]   ● Dados oficiais TOTVS consultados em [horário]   [↻ Atualizar]
  [aviso caso os valores tenham ficado obsoletos / fonte indisponível]

IDENTIFICAÇÃO E CLASSIFICAÇÃO
Descrição [TERMINAL OLHAL M5 ..._______________________________________]  (editável)
Grupo     [1008 — descrição oficial ▼]  Tipo [MP — ... ▼]  Unidade [PC — ... ▼]
[se mudou] ● Alterado  Antes: 1008 — ... → Agora: 1009 — ...  [↶ Desfazer]

ESTOQUE E CONTABILIDADE
Armazém [01 — ... ▼]   Conta contábil [11401002 — ... ▼]
Produto de terceiros [Não ▼]  Referência cliente [________________]
[se mudou] ● Alterado  Antes: ... → Novo: ...  [↶ Desfazer]

FORNECEDORES — AMARRAÇÕES OFICIAIS DO PRODUTO (SA5)
[+ Adicionar fornecedor] (abre busca colapsável SA2 aprovada no D11)
  [⌕] CÓDIGO  LOJA  RAZÃO SOCIAL           NOME FANTASIA   PART NUMBER [EDITÁVEL] CATÁLOGO [EDITÁVEL] AÇÕES
  [⌕] 000002  01    TE CONNECTIVITY...     TYCO            [880643-1_________]      [_________]          [🗑]
  [⌕] 000009  01    WIREX CABLE ...        —               [201.1750.00______]      [_________]          [🗑]
  [⌕] 000972  01    DELPI COMPONENTES     —               [10080022________]      [_________]          [🗑]
  [se mudou] ● Alterado: PN 880643-1 → 880643-2 (só vínculo 000002/01)
  [se novo]   + Adicionado: fornecedor 001572/01
  [se remove] − Remoção proposta: fornecedor 000972/01  [↶ Desfazer exclusão]

ALTERAÇÕES DETECTADAS AUTOMATICAMENTE: 1 campo SB1, 1 vínculo SA5 modificado, 1 adicionado, 1 remoção proposta
[Voltar] [Revisar e enviar]
```

**Rótulos e cores:** valor sem alteração = normal; valor alterado = realce informativo com indicador textual `Alterado` e before→after; novo vínculo = `Adicionado`; exclusão proposta = `Remoção solicitada`, estado riscado/desabilitado/reversível até envio, sem remoção física. Não depender só de cor. Nenhuma string/código de exemplo deve ser fixado no runtime.

## 3. Modelo de estado e diff — frontend

Manter dois conjuntos de dados **separados**, imutáveis em sentido funcional:

1. `officialBaseline` — retorno autorizado de `GET .../reference-data/products/{code}/edit-context` com `source`, `readAt`, `linksComplete`, código, campos SB1 e SA5 (incluindo PN/Catálogo). Não mutar ao digitar; refresh explícito deve detectar baseline alterado e permitir reconciliação, não apagar edições silenciosamente.
2. `workingCopy` — valores editáveis atuais e operações de vínculo; as linhas SA5 possuem **chaves estáveis por produto e fornecedor**, não índices.

**Diff puro, testável, derivado em uma função única** (não armazenar selectedPaths manual):
- **SB1 update**: `changed = !equal(canonicalize(working[field]),canonicalize(baseline[field]))`, com normalização **por campo e contrato** (códigos com zeros à esquerda devem permanecer strings; não usar trim/case-fold de forma indiscriminada; preservar semântica de `""`, `null`, não retornado, zero e `false`).
- Campos iguais ao oficial não geram `changes[]`; retornar ao valor original remove o diff. Não enviar valor oficial e justificativa de campo não modificado.
- **SA5 update**: comparar linha selecionada por identidade oficial `(supplierCode,store)` mais contexto de produto/filial definido pelo owner; somente diferenças em `partNumber` e `catalogNumber` entram em `fields`. Abrir/fechar busca não cria diff. `""` explícito pode significar limpar; atributo ausente significa não alterar.
- **SA5 add**: seleção de fornecedor SA2 cuja chave não esteja no baseline e não esteja adicionada duas vezes; adicionar ao workingCopy e produzir `operation:"add"` com os atributos necessários, podendo **ambos PN e Catálogo ser vazios** quando a fonte/regra permitir. Necessário contrato backend compatível (hoje validação rejeita fields vazios).
- **SA5 remove**: excluir visualmente uma chave que constava em baseline mediante **ação explícita de lixeira** (não interpretar ausência acidental durante carregamento como remoção). Criar tombstone/local `operation:"remove"` com before, reason e possibilidade de **Desfazer** antes do envio. Nunca acionar write ERP; desabilitar operação se incompletude/ambiguidade oficial. Remover uma linha recém-adicionada (não existente no baseline) simplesmente cancela o `add`; não gera `remove` do ERP.
- Cancelar/desfazer mudanças isoladas e globais; restaurar baseline preservado. Não descartar motivo já escrito numa edição sem informar quando necessário.
- Ao mudar o código do produto na etapa 1: resetar contexto/workingCopy somente com confirmação se havia alterações não enviadas.
- Busca por fornecedor existente para `add` mantém D8–D11: lupa, input colapsável, overlay oficial, pesquisa SA2 remota por código/razão/fantasia, seleção obrigatória, identidade completa, sem clipping.

**Justificativa:** no momento de editar, não exigir uma justificativa extra para simplesmente digitar. Na etapa **Revisar e enviar**, exigir justificativa **por operação efetiva** (campo SB1 ou vínculo SA5 add/update/remove) antes de permitir o envio. Reutilizar justificativas do draft em retomadas. Sem diff efetivo = botão Enviar desabilitado e mensagem clara.

**Valor atual oficial visível:** o próprio campo é preenchido com o valor oficial. Quando diferente, apresentar auxiliar `Anterior no TOTVS: [valor]` e ação de desfazer. A fonte e hora da consulta ficam em banner compacto; não repetir `Atual no TOTVS` e mais outro input por campo.

## 4. Contrato backend e correções P0 (obrigatórias antes de liberar verificação)

### 4.1 Rota BFF de leitura — existente após D12, revisar

`GET /apps/engineering-api/v1/product-registration/reference-data/products/{officialCode}/edit-context`. Retorna snapshot SB1/SA5 com proveniência e completude. Backend-first RBAC `engineering.access`. `api-delpi` continua read-only:
- `GET /products/{code}?view=engineering` — SB1;
- `GET /products/{code}/suppliers?view=engineering` — SA5 com SA2, com paginação completa verificada;
- `GET /engineering/product-registration/suppliers?query=...` — SA2 na inclusão;
- catálogos oficiais já existentes para selects. Sem SQL no MFE/Engineering API.

### 4.2 Rota de intake/edição de proposta — estender, não duplicar

`POST /apps/engineering-api/v1/product-registration/intake/requests` e `PATCH /apps/engineering-api/v1/product-registration/requests/{id}/draft`. O backend deve aceitar propostas `changes[]` e `supplierLinkChanges[]` derivadas do diff, nunca confiar no diff do browser como prova de baseline ou autorização. Contrato versionado, sem trocar silenciosamente versão/semântica dos consumidores atuais. Manter `expectedVersion`, CAS, `Idempotency-Key`, auditoria, reason por operação, revisão técnica automática e compatibilidade com CREATE.

**Shape ilustrativa de operações candidatas (validar e formalizar pelo owner):**

```json
{
  "requestType": "update",
  "officialProductCode": "<codigo>",
  "changes": [{"path":"accountingAccount","proposedValue":"<novo>","reason":"<motivo>"}],
  "supplierLinkChanges": [
    {"operation":"update","key":{"supplierCode":"000002","store":"01"},"fields":{"partNumber":"<novo>"},"reason":"<motivo>"},
    {"operation":"add","key":{"supplierCode":"001572","store":"01"},"fields":{"partNumber":"","catalogNumber":""},"reason":"<motivo>"},
    {"operation":"remove","key":{"supplierCode":"000972","store":"01"},"reason":"<motivo>"}
  ]
}
```

**A operação `remove` é nova e constitui decisão PO de UX/solicitação**, não autorização de escrita ERP. O owner Engenharia deve confirmar pré/pós-condições da **ausência oficial SA5**, regras da filial, rollback e o tratamento de processos manuais ERP antes de habilitar submissão/verify para remoção. Não tratar remoção como simples omissão em lista nem criar endpoint `DELETE` em api-delpi. Se necessário, exibir o botão apenas como ação candidata desabilitada com explicação até fechamento do contrato técnico — entregar restante sem parar.

### 4.3 P0 — verificação SA5 obrigatória e fail-closed

**Evidência no código após D12**: `service.py` monta `changed_paths` de `changes[]` escalares, guarda `supplierLinkChanges` à parte; `_expected_verify_paths()` deriva paths apenas do `changed_paths`; `_compare()` só invoca `compare_link_ops()` dentro do caso `suppliers`. Logo, uma UPDATE contendo **apenas operações SA5** pode não verificar a SA5 e poderia ser concluída sem read-back dos links. **Corrigir primeiro como P0; testar a falha e sua correção no workflow real.**

Requisitos:
1. Derivar o conjunto de verificações de todo change set aprovado — escalares **mais** operações SA5; nunca permitir `completed` se qualquer operação não verificada, ausente ou ambígua.
2. `verify_and_complete` relê SA5 por api-delpi e exige evidência de linksComplete/valores oficiais; `unverifiable` **não** é match.
3. Para `update`, chave única e cada atributo modificado idêntico ao oficial, inclusive `""` vs valor preenchido; atributos não mudados/vínculos não-alvo fora do diff.
4. Para `add`, baseline autorizado congelado comprova **ausência anterior** (inclusive lista completa), read-back comprova **presença posterior única** e atributos; se já existia no baseline, `duplicate_link` e bloqueia. Sem baseline persistido, não declarar add comprovado.
5. Para `remove`, baseline autorizado comprova **presença anterior** e read-back oficial completo comprova **ausência posterior**; se ainda existir, mismatched; se consulta incompleta ou chave ambígua, fail-closed. Não reintroduzir comparação de lista integral para os outros links.
6. Nomes/forma de eventos e revisão imutável devem representar add/update/remove seletivos, com before/after, reason, timestamp, actor e provenance, sem apagar vínculos alheios. Não alterar revisões já publicadas.
7. Reforçar validação **add com PN/Catálogo vazios**: fields opcionais/empty, sem permitir add sem chave oficial, motivo, baseline e evidência; diferenciar `fields={}` admitido para `add` quando atributos opcionais de `update` sem mudanças (proibir no update).
8. Testar via REST e service **UPDATE apenas SA5**, com resultado oficial divergente/incompleto/ambíguo e garantir `verification != matched`, `no revision`, `request != completed`.

**Backend não deve usar a UI como autoridade de diff.** Comparar proposta com snapshot baseline oficial verificável, detectar no-op/unchanged, entradas adulteradas, conflitos e stale snapshot. A leitura inicial não é confirmação de publicação posterior. Não existe lock distribuído Postgres–TOTVS; exigir reconciliação/409 para concorrência relevante, sem rebase silencioso.

## 5. Read/write/draft/publish e autorização

`Portal/EVA → Engineering API → api-delpi → TOTVS`. O MFE propõe, a Engineering API registra draft, operador do TOTVS realiza mudança oficial em canal próprio e `verify-and-complete` publica somente após comprovação. Não alterar SSO, owners, directAccessGrants nem criar MCP tools além das seis existentes. `engineering.access` dá CRUD operacional, `engineering.manager` governa funções administrativas se implementadas; todas as escritas fail-closed, `allowedActions` respeitados. Dados oficiais e referências devem ter origem, hora, escopo e completude. Nenhum SQL/ODBC TOTVS na Engineering API.

## 6. Composição visual e plugin-ui

Componentes existentes a reutilizar após conferir exports/propriedades reais: `PageHero`, `SectionCard`, `EngineeringSearchableSelect`/`createDashboardSelectField`, `TextField`, `FormActions`, `StateBanner`, `DataTableSection` ou tabela semântica quando edição célula for inadequada ao kit, `AnchoredPanelPortal`, `HostContainedModal` para confirmação de remoção quando necessário, ícones Lucide (`plus`, `search`, `trash-2`, `undo-2`, `pencil`). Usar façade `engineeringUi.ts` sem criar um kit paralelo.

Desktop: campos em grid responsiva, cada campo um controle com valor atual preenchido; alteração apresenta indicador e before embaixo, sem input duplicado. Fornecedores em tabela editável com PN/Catálogo na linha, ações compactas. Tablet: scroll interno da tabela sem clipping do popover. Mobile: cards por vínculo, sem replicar dados, controles editáveis e estado de diff. Teclado/a11y: labels, `aria-live` para contadores, status textual, foco/restauração, 200% zoom, Enter/Space/Escape, confirmação de remoção, sem depender apenas da cor.

## 7. Sequência executável Devin (sem paradas para decisões já aprovadas)

**D13-0** Ler authorities e docs, `git status`/HEAD, inventariar implementações e diffs estrangeiros, contratos tipados, testes e baseline P0. `PROVEN/TO_INVENTORY`; código primeiro, nenhum rumor como fato.  
**D13-1 P0** Reproduzir bypass de verify para SA5-only; implementar correção fail-closed + baseline oficial, testes positivos/negativos e preservação de revisões. **Não prosseguir a declarar aceite UI sobre verificação vulnerável.**  
**D13-2 Domain/API** Fechar shape add/update/remove candidato, validadores, baseline, false changes, no-op, versionamento, errors, drafts CAS, timestamps/auditoria, espelhamento REST/EVA; remove somente com owner rule de ausência e aprovação técnica aplicável.  
**D13-3 MFE** Aplicar readContext→workingCopy→pure diff (SB1/SA5); retirar selectedPaths/checkboxes de UPDATE, manter CREATE; edição in-place, estados, desfazer e destaques; adição busca expansível D11, remoção proposta e reversível, review com justificativas.  
**D13-4 End-to-end** Testes contrato unit/service/PG real; auth/core; catálogos e SA2/SA5 via API; Playwright autenticado desktop/tablet/mobile, snapshots ilustrativos e screenshot real dos estados unchanged/changed/add/remove/reverted/review/error.  
**D13-5 DEV** Build/typecheck/vitest/pytest, containers oficiais afetados rebuild/up, migrate DEV se necessário, fingerprint bundle servido, smoke JWT+gateway+PG, docs/ledger/outcomes, commits e push conforme `AGENTS.md`. **Produção NÃO AUTORIZADA**.

Bloqueio específico sem credencial/owner: deixar função dependente `PENDING_OWNER`, nunca inventar PASS nem escrever ERP; prosseguir tudo que independe e apresentar residual preciso. Operações anteriores não serão reclassificadas `PROVEN` por documentação.

## 8. Matriz de aceite

| Cenário | Exigência |
|---|---|
| UPDATE campos SB1 | 1 campo editado diretamente = 1 change; retorno ao valor original = 0; demais intactos; códigos com zeros; justificar apenas diff |
| UPDATE vínculo SA5 | 1 PN/catálogo de 1 entre 3 = somente aquela chave/atributo; nenhuma mudança em outros |
| ADD SA5 | escolha SA2 real, chave ausente no baseline oficial, PN/catálogo ambos vazios permitido se regra legítima; read-back presença posterior |
| REMOVE SA5 | ação explícita, visual reversível, reason, baseline presença, read-back ausência, outros intactos; **nunca ERP write por API** |
| SA5-only verify P0 | matched somente com todas ops comprovadas; missing/mismatched/ambiguous/incomplete/unverifiable não concluem nem publicam revisão |
| Baseline / concorrência | refresh não apaga mudanças, 409 e reavaliação; no-op não vira proposta; read-current identificado |
| UX | sem checkboxes UPDATE; não duplicar input para cada campo; diff textual antes→depois, contagens, desfazer, mobile |
| Segurança | 401/403/503 fail-closed, no bypass via campo oculto, AuthZ backend, same REST/EVA use cases, 6 MCP tools |
| Cobertura | Typecheck+build+Vitest+pytest+PG real+Playwright 3 form factors; screenshots/acceptance PO |
| DEV | containers realmente atualizados, bundle fingerprint validado, Gateway JWT real; sem PROD |

**Status:** decisão UX aprovada, implementação pendente. A mudança de `remove` exige fechar regra de negócio e postcondition dentro dos owners já existentes; se alterar authority, `ARCHITECTURE_DECISION_REQUIRED` antes da operação proibida.


## 9. D14 — Justificativas individuais opcionais e busca V2 completa

[D14 — contrato canônico de busca colapsável e justificativas por atributo](./MFE-PRC-D14-COMPLETE-SUPPLIER-LOOKUP-AND-OPTIONAL-REASONS.md). **D14 supersede** qualquer frase anterior que exija motivo obrigatório por alteração de campo ou fornecedor, salvo política técnica explícita de owner para operação de remoção. Cada campo SB1 e cada PN/Catálogo SA5 tem botão independente, textarea opcional de 250 caracteres, contador, recolher/remover; operation ADD/REMOVE possui razão separada. Não reaproveitar supplierReason geral. O modo UPDATE segue edição direta e diff automático, e CREATE recebe a mesma tabela de busca colapsável. D13 no código deve ser revisado para garantir verificação SA5-only fail-closed e baseline antes/depois de ADD/REMOVE. **D14_IMPLEMENTATION_PENDING; produção suspensa.**
