# PRC-REF-023 — Validação CREATE e UX unificada de devolução/correção

> **Decisão funcional do owner — 11/11/2026** · **Status: TARGET / implementação pendente**.
> **Issue canônica:** [delpi-central#154](https://github.com/roberiooliveiradev/delpi-central/issues/154).
> **Escopo:** Engineering API, \`@delpi/plugin-ui\`, Portal Engenharia e Minhas Solicitações. **Sem** segundo chamado, API paralela, papéis novos ou escrita TOTVS.
> **Nota de precedência:** este documento registra as decisões atuais do fluxo PRC Engineering API × dois MFEs. O planejamento de migração legado em \`EVOLUCAO.md\` descreve proposta histórica/futura e não autoriza substituir esta autoridade vigente por \`requests-api\`.

## 1. Situação verificada vs. decisão

**PROVEN por inspeção de main (11/11/2026):**
- \`engineering-api/.../domain/product_registration/catalog.py\`: \`FIELD_SPECS\` marca \`suppliers\` como \`required_create_intake=True\`, mas o comentário atual diz "array presente (pode ser vazio)" e \`validate_create_payload\` aceita lista vazia. \`validate_supplier\` exige atributos por vínculo, incluindo PN conforme catálogo, **não** cardinalidade mínima do array.
- \`plugins/plugin-ui/src/components/prc/PrcRequestForm.tsx\`: \`validateStep\` ignora \`spec.kind === "suppliers"\` na checagem de required; valida linhas inválidas e PN faltante, mas não comprova \`suppliers.length >= 1\`.
- \`engineering-api/.../domain/product_registration/correction_returns.py\`: alvos de devolução atuais \`FIELD\` ou \`SUPPLIER_LINK\`; \`validate_return_targets\` proíbe \`FIELD:suppliers\` e exige \`supplierKey\` para \`SUPPLIER_LINK\`. \`service.return_for_correction\` confirma que o vínculo alvo existe. \`validate_supplier_correction\` preserva identidades e não permite add/remove de vínculos durante devolução.
- \`plugins/plugin-ui/src/components/prc/PrcCorrectionTargets.tsx\`: seleção e edição granular já compartilhadas para campos e vínculos existentes; **não** é autorização de inclusão relacional.
- Os dois MFEs já consomem \`PrcRequestForm\` compartilhado; os componentes de devolução/correção estão parcialmente compartilhados, mas ainda há composição distinta no detalhe Engenharia × My Requests.

**TARGET decidido:** nenhum **novo CREATE de matéria-prima** pode ser submetido ou salvo como ficha válida sem **pelo menos um vínculo de fornecedor oficial válido, com código+loja e Part Number não vazio**. Catálogo é opcional. Validar no cliente e, autoritativamente, na Engineering API. A regra de UPDATE é distinta e mantém baseline/ops SA5 e seus invariantes oficiais.

## 2. Matriz de negócio e invariantes

| Operação/estado | Regras obrigatórias |
|---|---|
| CREATE, rascunho em tela antes do envio | UI aponta ausências; para avançar à revisão/enviar requer todos os campos \`requiredCreateIntake\`, **mínimo um fornecedor válido** e PN em cada vínculo |
| CREATE, intake oficial | Engineering API rejeita lista \`suppliers=[]\`, \`null\`, ausência do path, vínculos incompletos, PN vazio, código/loja inválidos ou duplicados, conforme contrato; não basta \`required\` HTML |
| CREATE, edição do caso \`submitted\` pelo criador | \`PATCH /draft\` não pode salvar estado final inválido ou remover o último fornecedor; preservar CAS, versão, idem, objeto e histórico |
| CREATE, iniciar atendimento | Verificar consistência mínima para casos existentes, sem criar bypass; a política de saneamento legado deve preservar casos incompletos e evitar deadlock |
| UPDATE de produto | **Não** impor cegamente a cardinalidade de CREATE. Validar modificações/baseline oficial e \`supplierLinkChanges\` pelas regras próprias |
| \`in_progress\` | Ficha e anexos RO; analista conserva apenas workflow técnico autorizado |
| \`needs_correction\` | Corrigir **somente** os alvos devolvidos; revalidar resultado conforme regras aplicáveis e política de legado; não abrir edição geral |
| \`completed/rejected\` | Sem escrita de ficha/anexos |

O domínio determina que "fornecedor oficial válido" significa identidade obtida/validada pelo contrato de fornecedor autorizado, sem confiar em nome digitado como prova de existência. Preservar zeros à esquerda na chave \`supplierCode + store\`. Catálogo opcional e PN obrigatório para os vínculos informados em CREATE.

**Compatibilidade:** casos históricos incompletos não devem ser excluídos, reescritos silenciosamente ou tornados impossíveis de resolver. Documentar e testar uma política governada de saneamento; caso exija novo alvo/ação de inclusão, submetê-la ao owner antes de ampliar REF-022. A nova regra nunca pode permitir novos CREATE inválidos.

## 3. Modelo universal de seleção/correção (não "motor de fornecedores")

**Princípio:** elegibilidade de alvo independe de valor preenchido. **Não** inferir permissões de presença, ausência ou da UI. O contrato do owner define alvo estável, tipo de dado, operações permitidas e validadores. Generalização pragmática, sem framework universal especulativo.

| Forma real | Apresentação no modal | Operação governada |
|---|---|---|
| Campo escalar, preenchido ou vazio | Linha com checkbox, valor atual/ausente e motivo obrigatório ao marcar | Corrigir/confirmar valor |
| Campo composto real | Grupo expansível, seleção de atributo elegível | Corrigir/confirmar atributo |
| Tabela com linhas | Tabela com chave estável, seleção de célula ou operação de linha | Corrigir atributos; inserir/remover/substituir **somente se o domínio suportar** |
| Tabela vazia | Estado vazio **visível**, com operação genérica de inclusão **somente se aplicável e contratada** | Nunca ocultar automaticamente a seção por falta de registros |
| Documentos | Consultar/download; complemento só se contrato de alvo documental existir | Upload em \`needs_correction\` segue bloqueado até aprovação |

A **tabela de fornecedores é uma instância** do padrão de linhas: chave \`supplierCode + store\`; PN e catálogo são atributos; identidade não pode virar campo livre porque um checkbox de vínculo foi marcado. Não criar seção fixa "fornecedor ausente" para o fluxo normal novo: o CREATE inválido deve ser barrado **antes** do atendimento. No legado, a tabela vazia precisa de fallback/regularização governada, não omissão silenciosa.

## 4. Wireframe A — modal Engenharia: Devolver para correção

\`\`\`text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ Devolver para correção                                                        [X]  │
│ Selecione qualquer dado elegível, preenchido ou vazio; motivo por alvo obrigatório. │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ IDENTIFICAÇÃO E CLASSIFICAÇÃO                                                       │
│ [ ] Descrição           Atual: TESTE                                                 │
│ [x] Grupo               Atual: 1008                                                  │
│     Motivo * [Grupo informado não corresponde ao item._________________]            │
│ [ ] Tipo                Atual: MP                                                    │
│ [ ] Unidade             Atual: PC                                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ ESTOQUE E CONTABILIDADE                                                              │
│ [ ] Armazém padrão      Atual: 01                                                    │
│ [ ] Conta contábil      Atual: 11401002                                              │
│ [ ] Produto terceiros   Atual: Não                                                   │
│ [x] Referência cliente  Atual: — (vazio)                                             │
│     Motivo * [Preencher referência solicitada.________________________]             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ TABELAS E RELACIONAMENTOS                                                           │
│ Fornecedores — 2 vínculos (exemplo; não é tipo de alvo universal fixo)               │
│ ┌─────────┬──────┬────────────────────┬──────────────────┬────────────────────┐        │
│ │ Código  │ Loja │ Razão social       │ Part Number      │ Catálogo           │        │
│ │ 000002  │ 01   │ TE CONNECTIVITY    │ [x] TESTE999     │ [x] —              │        │
│ │ 000145  │ 01   │ OUTRO FORNECEDOR   │ [ ] ABC123       │ [ ] CAT998         │        │
│ └─────────┴──────┴────────────────────┴──────────────────┴────────────────────┘        │
│ Motivo * 000002/01 · Part Number [Divergente.____________________________]          │
│ Motivo * 000002/01 · Catálogo    [Verificar catálogo.____________________]          │
│ Tabela vazia (legado/outros tipos reais): "Nenhum registro"; não esconder seção;    │
│ operações de inclusão apenas quando definidas/autorizadas pelo owner.              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ RESUMO: 2 campos escalares + 2 atributos/1 linha · 0 motivos pendentes              │
│ Observação geral (opcional) [____________________________________________]          │
│                                                     [Cancelar] [Devolver correção]   │
└─────────────────────────────────────────────────────────────────────────────────────┘
\`\`\`

**Interação:** checkboxes múltiplos; motivo individual obrigatório (mínimo conforme contrato atual); não enviar sem alvo ou com motivo ausente; motivos indexados por chave estável mesmo com sort/filter; seleção de linha **não** libera tudo; formulário com scroll interno, header/footer acessíveis, foco/teclado/ARIA, light/dark, mobile e zoom 200%.

## 5. Wireframe B — card de correção/reenvio: ambos os MFEs

\`\`\`text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ Corrigir campos devolvidos                          [Devolvida para correção]        │
│ Apenas campos/registros formalmente devolvidos são editáveis.                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ IDENTIFICAÇÃO / ESTOQUE                                                              │
│ Grupo · motivo: "Grupo incorreto"                                                    │
│ Original: 1008  Novo valor: [Select oficial ▼]                                     │
│ Referência cliente · motivo: "Preencher referência"                                 │
│ Original: —     Novo valor: [__________________]                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ FORNECEDORES (mesmo renderer genérico de tabela/atributo)                           │
│ Código/Loja  Razão social          Part Number           Catálogo                    │
│ 000002/01    TE CONNECTIVITY       [TESTE999_____]         [___________]               │
│                                 motivo: divergente    motivo: verificar              │
│ 000145/01    OUTRO FORNECEDOR      ABC123 (RO)            CAT998 (RO)                 │
│ Demais células e linhas: SOMENTE LEITURA; identidade não é texto livre.             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ RESUMO ANTES DO REENVIO                                                              │
│ Grupo: 1008 → novo valor; Referência: — → novo valor                                │
│ 000002/01 PN: TESTE999 → novo valor; Catálogo: — → valor/confirmado                  │
│ Erros por campo/célula; conflitos de versão solicitam reload.                       │
│                                                [Cancelar] [Salvar e reenviar]        │
└─────────────────────────────────────────────────────────────────────────────────────┘
\`\`\`

**Paridade:** os mesmos componentes render-only e controls neutros de \`@delpi/plugin-ui\` para o card de correção na experiência apropriada em Engineering e My Requests; containers apenas adaptam dados, navegação e operações permitidas. A Engenharia não recebe autorização de editar em nome do criador só por reutilizar o renderer.

## 6. Boundaries / contratos antes da implementação

- \`@delpi/plugin-ui\`: formulário \`PrcRequestForm\` e componentes de seleção/edição de alvos; elevar reutilização de apresentação **sem** incluir HTTP, tokens, estado oficial, provider scope ou autoridade.
- Engenharia / My Requests: wrappers mínimos e adapters para Engineering API, mesmo formulário CREATE/UPDATE e mesma representação de alvo/erro; **não** copiar implementações completas por MFE.
- Engineering API: fonte final de required/enum/allowlist, chave de registro, validação por operação, target, AuthZ de objeto, estado, versão/CAS, idempotência, histórico, persistência e workflow. Proibir edição geral em \`in_progress\`.
- Core = RBAC; Keycloak = identidade; TOTVS = cadastro oficial consultado; sem escrita automática.
- REF-022 atual **não permite inclusão/remoção de fornecedor devolvido**; \`SUPPLIER_LINK\` sem \`targetAttribute\` só autoriza atributos editáveis do vínculo existente. Mudança dessa semântica exige contrato/owner e preservação de compatibilidade. **ARCHITECTURE_DECISION_REQUIRED** caso se pretenda criar novo tipo de alvo/operation de inclusão para saneamento legado.
- Não generalizar "tabela de clientes" inexistente. O mecanismo deve ser adaptável a tabelas reais adicionais após inventário/Abstraction Gate.
- API deve responder erros de validação claros e campos/endereço de falha; não confundir ausência de dado com autorização.
- Sem novo BFF quando o adapter autorizado da Engineering API satisfaz o caso.

## 7. Critérios de aceite — TARGET (não executados)

1. CREATE sem fornecedores: bloqueado em revisão/envio pela UI **e** rejeitado pelo backend; com um fornecedor sem PN: bloqueado; catálogo vazio: permitido.
2. CREATE com vínculo válido, código+loja oficiais, PN e demais required: passa pelas validações; UPDATE mantém regras próprias.
3. \`submitted\`: criador não remove último fornecedor nem salva criação inválida por \`PATCH /draft\`; terceiro e analista não burlam object AuthZ; CAS/version/idem testados.
4. Modal mostra campos escalares elegíveis vazios/preenchidos, seleção múltipla e motivo por alvo; dados obrigatórios inviáveis não chegam novos ao atendimento.
5. Tabelas reais mostram linhas e atributos por chave estável; motivo não migra de célula após ordenar; tabela vazia visível com operação apenas contratada.
6. Card de correção exibe valores anteriores, motivos e editores tipados; permite somente alvo devolvido; os dois MFEs usam composição/renderer compartilhado.
7. Reenvio endereça todos os alvos e preserva requestId, audit trail, versão/idempotência. Não permite fornecedor diferente, atributo não devolvido ou gravação durante \`in_progress\`.
8. Casos legados vazios permanecem legíveis; regularização não bloqueia perpetuamente nem inventa direito de inclusão; política de saneamento deve ser documentada/testada, com decisão formal se mudar contrato.
9. Zero alteração de banco/roles/workflow paralelo/TOTVS; nenhuma duplicação de API ou formulário.
10. Testes positivos/negativos backend (intake, PATCH, concorrência, 3 usuários, devolução e reenvio) + frontend/kit/hosts + E2E autenticado e screenshots desktop/mobile/zoom 200%; resultados não executados = \`TEST_NOT_RUN\`.
11. Visual consistente: cards espaçados, modais acessíveis, motivos por alvo, erros junto ao campo, sem overflow e respeitando tema.
12. Compatibilidade de REF-020/022/023 e casos históricos, sem regressão de CREATE/UPDATE ou anexos.

## 8. Fluxo de execução governada

\`HEAD → git status → AGENTS.md → fontes oficiais → contratos → matriz RQ/AC → menor diff backend-first → testes no SHA → rebuild DEV → evidência E2E → residual search → ledger/issue\`.

**Status:** documento de decisão/target, **não** evidência de implementação. A issue #154 permanece aberta; E2E autenticado prévio segue \`TEST_NOT_RUN\`.

---

## 8. Registro de execução — CORRECTION-10 (11/11/2026)

**Status: PROVEN por testes (backend + kit + MFEs) — E2E autenticado pendente.**

Implementado no fluxo descrito neste documento:

- **Backend (autoridade):** `validate_create_payload` rejeita
  `suppliers=[]` (`fields.suppliers=required`), `null` e path ausente;
  `validate_supplier_list` rejeita duplicidade `(supplierCode, store)`
  no intake e no `PATCH /draft`; `update_draft` impede remover o último
  vínculo de caso CREATE em `submitted` — somente quando `suppliers`
  está no change set (legados incompletos seguem editáveis em outros
  campos, sem deadlock retroativo). UPDATE preserva baseline/ops SA5.
- **Kit `@delpi/plugin-ui`:** `PrcRequestForm` bloqueia avanço/envio de
  CREATE sem fornecedor (mensagem contextual + `fieldErrors.suppliers`);
  `PrcCorrectionTargetSelector` ganhou `draft` (linha «Atual:», vazio
  também é alvo), `group` por campo (seções canônicas
  `PRC_FIELD_GROUPS`/`PRC_FIELD_GROUP_BY_PATH`, extraídas de
  `utils/prcProductRegistration` para os 3 consumidores) e estado vazio
  visível da tabela de fornecedores; `PrcTechnicalSheetView` e
  `PrcRequestForm` passaram a consumir `PRC_FIELD_GROUPS`.
- **Engenharia:** modal recebe `draft` + grupos e orientação do
  wireframe; `PrcTechnicalSheet` em `needs_correction` agora renderiza
  o mesmo `PrcReturnedFieldsEditor` do kit usado por Minhas
  Solicitações — implementação vertical inline removida (~200 linhas).
- **Testes:** `tests/test_prc_ref023_correction10.py` (8 casos:
  lista vazia/nula/ausente/duplicada, catálogo opcional, remoção do
  último vínculo, sem-PN no patch, legado sem deadlock);
  +2 casos no kit (seções/«Atual:»/estado vazio) e +1 form editCase;
  +3 estruturais no modal/ficha da Engenharia.
- **Compatibilidade:** contrato `/returned-fields`, `return-for-correction`,
  CAS `expectedVersion`, `Idempotency-Key`, `requestId`, AuthZ por
  objeto e histórico inalterados — zero mudança de rotas/DTOs/migrations.
- **Pendente:** E2E autenticado com screenshots (TEST_NOT_RUN);
  issue #154 atualização depende de credenciais gh.
