# PRC-REF-012 — Edição individual de campos e amarrações produto × fornecedor

**Status:** `PO_DIRECTION_APPROVED / ARCHITECTURE_CONTRACT_DESIGN / IMPLEMENTATION_PENDING / PRODUCTION_DEPLOY_SUSPENDED`  
**Data:** 2026-11-08 · **Origem:** feedback PO em screenshot DEV do wizard UPDATE.  
**Owners:** Portal Engenharia (UX), Engineering API (aplicação/solicitações/revisões), api-delpi (read oficial TOTVS); TOTVS permanece source of truth; owner Engenharia aprova regras técnicas e publicação.

## 1. Problema comprovado no HEAD

Na página `plugins/engineering/src/features/product-registration/pages/PrcCreatePage.tsx`, o modo UPDATE oferece checkbox **Alterar vínculos de fornecedores** e texto **A lista informada substitui os vínculos desta solicitação**. `buildBody()` envia uma única change `{path:"suppliers", proposedValue: suppliers.map(...), reason}`, em vez de operações por vínculo. A tela mostra linhas vazias e exige justificativa única para a lista.

A Engineering API em `engineering-api/engineering_app/domain/product_registration/catalog.py` define `suppliers` como `kind="suppliers"`, e `validate_update_changes()` aceita uma única change por path. `compare_suppliers()` considera vínculos oficiais adicionais como `unexpected_in_official`, ou seja, atualmente verifica a lista inteira. A gateway `engineering-api/.../infrastructure/gateways/official_product_reader.py` consulta os vínculos oficiais através do `GET /products/{code}/suppliers?view=engineering` da api-delpi. Os vínculos oficiais estão associados à relação produto-fornecedor **SA5**; cadastro mestre do fornecedor **SA2** é uma fonte distinta para a busca de fornecedor.

**Falha de produto:** o usuário quer adicionar ou modificar apenas um vínculo SA5 de um produto, não reescrever toda a sua relação de fornecedores. Também quer alterar qualquer campo simples de produto individualmente.

## 2. Boundary e autoridade preservados

- **SB1/TOTVS:** dados mestres do produto; **SA2/TOTVS:** cadastro mestre de fornecedores; **SA5/TOTVS:** amarrações produto × fornecedor (incluindo atributos como Part Number, Catálogo quando suportados pela projeção oficial).
- A tabela SA5 é **a relação oficial**, não uma tabela do Portal. Confirmar no source canônico api-delpi os nomes físicos e a cardinalidade/chave exata; **não inventar nomes de colunas, filial/loja adicionais ou regras de unicidade**.
- A Engenharia cria **solicitação DRAFT/CANDIDATE**, não executa cadastro/alteração no TOTVS. O operador autorizado faz a operação oficial no ERP, e a Engineering API reconsulta via api-delpi antes de concluir.
- `Portal/EVA → Engineering API → api-delpi → TOTVS`. Não usar SQL direto em Engineering API, browser ou EVA; não modificar ERP neste escopo.
- Permissões: `engineering.access` para fluxo operacional, `engineering.manager` apenas administração; live AuthZ no backend e `allowedActions`/workflow/CAS/idempotência/auditoria preservados.
- Nova tabela Engineering de amarração como source of truth **não é necessária**; as solicitações registram mudanças candidatas e snapshots imutáveis. Se inventário exigir mudar owner/source of truth/bounded context, `ARCHITECTURE_DECISION_REQUIRED` e retorno à Coordination.

## 3. Requisitos de domínio: UPDATE seletivo e vínculo seletivo

### 3.1 Campos simples

Continuar usando `changes[]` com `{path, proposedValue, reason}` para cada campo SB1 selecionado; a change set tem somente paths efetivamente modificados. Form pré-carregado com snapshot oficial vigente, e não valores vazios que possam acidentalmente apagar outros campos. Comparação/revisão deve conservar todos os demais campos. O usuário não informa revisão-base manualmente; backend resolve revisão técnica atual e aplica concorrência/409.

### 3.2 Operações por vínculo SA5 (modelo candidato; NÃO endpoint atual)

Propor contrato tipado de `supplierLinkChanges[]` ou `changes[]` especializado, com payload mínimo por operação, **após inventário e aprovação de contrato pelo owner Engineering API**:

```json
{
  "requestType": "update",
  "officialProductCode": "<codigo-oficial>",
  "supplierLinkChanges": [
    {
      "operation": "update",
      "key": {"supplierCode": "<codigo>", "store": "<loja>"},
      "fields": {"partNumber": "<novo-valor>"},
      "reason": "Atualização do Part Number do fornecedor"
    },
    {
      "operation": "add",
      "key": {"supplierCode": "<codigo>", "store": "<loja>"},
      "fields": {"partNumber": "", "catalogNumber": "<referencia>"},
      "reason": "Adicionar novo fornecedor para este produto"
    }
  ]
}
```

Este JSON é **proposta ilustrativa de application contract**, não documentação de rota/payload existente. Nomear a shape definitiva após verificar compatibilidade com os 18 endpoints, `validate_update_changes()`, `update_draft`, REST/EVA e persistence JSONB.

**Operações aprovadas nesta direção:**
- `update`: um vínculo SA5 já existente, selecionado pela identidade oficial, e só os atributos presentes em `fields`; não sobrescrever campos ausentes.
- `add`: criar uma **proposta** de novo vínculo SA5 para fornecedor SA2 existente, sem tocar os outros vínculos.
- `remove`: **NÃO APROVADO NESTE REFINAMENTO**. Não adicionar exclusão sem decisão explícita de owner/PO.
- Alterar fornecedor/loja de vínculo existente não equivale a editar texto da razão social; tratar como nova amarração candidata e submeter a decisão de remoção da antiga, se necessária.
- Identidade corrente validada pelo contrato: `(supplierCode, store)`, preservar zeros à esquerda e diferenciar loja; se o TOTVS requer filial/seq adicional na chave, owner deve confirmar e atualizar contrato formalmente.
- Um mesmo vínculo não deve receber operações conflitantes na mesma solicitação.
- Part Number opcional: `""` significa vazio legítimo, mas **ausência da propriedade** significa não alterado; `null` exige semântica explícita acordada. A diferença entre **não alterar** e **limpar** é obrigatória.
- Catálogo opcional: mesma distinção entre ausente/nulo/vazio, conforme contrato oficial.
- Não validar só pelo texto: fornecedor e loja devem ser selecionados por SA2 oficial, com eventual leitura SA5 atual.
- As alterações devem carregar **justificativa individual** e expected version; audit log com before/after, ator, operação, chave e proveniência da leitura.

### 3.3 Conclusão/verificação seletiva

A implementação atual `compare_suppliers()` compara o conjunto e marca `unexpected_in_official` para vínculos não enviados. **Isso precisa mudar para UPDATE seletivo**.

- `update`: buscar vínculo SA5 oficial pela chave, rejeitar missing/ambiguous/unverifiable; verificar **somente os atributos explicitamente alterados** frente aos valores oficiais, incluindo PN e catálogo quando selecionados; conferir pré-condições/baseline para prevenir conflito de edição.
- `add`: garantir que a nova amarração não existia no baseline/estado prévio autorizado; após a operação manual, reconsultar e comprovar a presença e atributos propostos na SA5. Não tratar um vínculo já existente como sucesso de add.
- Os demais vínculos SA5 oficiais ficam fora do conjunto de mudança e **não** produzem `unexpected_in_official`; preservar sua integridade/provenance sem exigir recadastrá-los.
- Se um vínculo não-alvo mudar concorrente no TOTVS, registrar freshness/snapshot e não reescrever seu valor; definir se isso impacta conclusão conforme política do owner, com evidência.
- Sempre reconsultar o oficial pela api-delpi no `verify_and_complete`, falhar fechado em unavailable, 403, absent field, mismatch ou evidência insuficiente; revisão candidata só publicada quando postcondição total da solicitação for comprovada.
- Na criação de produto (CREATE), manter fluxo de ficha completa e verificação do conjunto de vínculos quando aplicável: não mudar sem testes de regressão explícitos.
- Persistir mudança candidata e seus eventos, inclusive diff de SA5 por operação, sem adulterar revisões imutáveis antigas. Se schema/tabela/DTO requer migração, V014+ owner e testes, nunca mutate das V012/V013 aplicadas.

## 4. Wireframe operacional — tela UPDATE

```text
Alterar produto oficial [código]    [dados oficiais carregados · última revisão técnica automática]

IDENTIFICAÇÃO E CLASSIFICAÇÃO
[ ] Descrição                     [ ] Grupo             [ ] Tipo             [ ] Unidade
    Somente campos marcados e efetivamente modificados entram no change set.
ESTOQUE E CONTABILIDADE
[ ] Armazém padrão                [ ] Conta contábil    [ ] Produto de terceiros    [ ] Referência cliente

FORNECEDORES  —  Amarrações oficiais deste produto (SA5)
[+ Adicionar vínculo]                                  [Atualizar vínculos]
  [🔎] CÓDIGO   LOJA   RAZÃO SOCIAL            PART NUMBER       CATÁLOGO           AÇÃO
  [🔎] 001572   01     3RHO INTERRUPTORES...   PN ATUAL          CAT ATUAL          [✎ Alterar]
  [🔎] 000002   01     TE CONNECTIVITY ...     —                 CAT ATUAL          [✎ Alterar]
  (ao clicar Alterar em uma linha:)
    Alterar vínculo 000002/01   [ ] Part Number   [ ] Catálogo
    Part Number atual: —        Novo: [...................]     Motivo: [........]
    [Descartar edição]                                    [Aplicar na solicitação]
  (ao clicar Adicionar vínculo:)
    Busca SA2 colapsável por código, razão social ou fantasia.
    Escolher fornecedor + loja, preencher PN/catálogo se necessário, motivo individual.
    [Cancelar]                                            [Adicionar à solicitação]

RESUMO DAS MUDANÇAS
  Campo produto: Conta contábil 114... → 115... | motivo ...
  Vínculo SA5 000002/01: somente Part Number vazio → XYZ | motivo ...
  Vínculo SA5 000089/01: ADICIONAR, catálogo opcional | motivo ...
[Voltar] [Revisar e enviar solicitação]
```

**Notas visuais:** em UPDATE, **não** renderizar 3 linhas vazias forçadas nem exigir edição/justificativa da coleção inteira; mostrar vínculos SA5 atuais, operações individualmente selecionadas, status `Sem alterações` nas linhas restantes. O wireframe V2 com colunas separadas e lupa expansível continua canônico para lookup, especialmente ADD. Usar plugin-ui (PageHero/SectionCard/Select/Checkbox/Table/IconButton/StateBanner), não criar design system paralelo.

## 5. Contrato, migração e provas antes da implementação

1. Inventariar `api-delpi GET /products/{code}/suppliers?view=engineering`, SQL/mapeamento SA5 oficial, supplier-key e retorno de campos (PN/Catálogo), including AuthN/AuthZ.
2. Inventariar `Engineering API` intake UPDATE, reference data, `validate_update_changes`, `update_draft`, repos PostgreSQL, diff e `verify_and_complete`; identificar exatamente onde `suppliers[]` hoje é substituído e onde há comparação de conjunto.
3. Definir contrato tipado **before implementation**: owner, request/response, errors (404/409/422/503), compatibility REST/EVA, idempotência, allowedActions, rollback/revoke, postconditions por operação, audit.
4. Provar **não-regressão**: campos SB1 por path, CREATE full supplier list, D5 optional PN, D7 catálogo e D8-D10 lookup SA2; nenhum write ao TOTVS.
5. Testes: `update PN` de um entre N sem alterar outros, `update catálogo`, `clear PN`, `add`, duplicata, fornecedor inexistente, versão stale, official mismatch, official missing attribute/unavailable, CAS, idempotência, seleção SA2 e verificação real-pg quando autorizado.
6. Browser: editar só Part Number de um fornecedor entre 3, confirmar preview com único diff, reload sem impacto dos demais, tentar adicionar nova SA5; registrar antes/depois e screenshots desktop/tablet/mobile.
7. **PRODUCTION_DEPLOY_SUSPENDED**; implantação DEV somente após testes e evidência. Não declarar `PASS` com simulação de mudança oficial TOTVS ou sem browser validado.

## 6. Decisões pendentes e gates

- Owner Engenharia deve aprovar contrato de alterações granulares SA5, chave oficial completa e política de compare seletivo vs CAS/freshness sobre lista.
- Operador TOTVS/owner da integração define processo manual para adicionar/editar amarração oficial SA5 e fornece cenários HML; sem simular escrita ERP.
- Remoção de vínculo **fora de escopo**, precisa decisão explícita PO.
- Necessidade eventual de nova migração, tipo de evento ou contrato oficial `api-delpi` exige mudança no owner correto, com testes e compatibilidade.
- Caso implique novo bounded context, owner ou source of truth: **`ARCHITECTURE_DECISION_REQUIRED`** para Coordination.

**Próximo incremento sugerido:** `ENG-PRC-D12-GRANULAR-SUPPLIER-LINK-CHANGE-CONTRACT-AND-UX`. Implementação somente após fechamento do contrato pelos owners. Não confundir documento PLANNED com capacidade PROVEN.


## 7. REF-012-A — Valor oficial atual visível antes de alterar

**Decisão complementar PO (2026-11-08): requisito obrigatório do modo UPDATE.** O usuário não deve adivinhar os valores vigentes. Ao informar o código oficial do produto, a Engineering API consulta **via api-delpi** os dados oficiais atuais de SB1 e os vínculos SA5 e apresenta-os como contexto de leitura autorizado, antes de o usuário escolher o que alterar. Esta leitura **não** altera TOTVS nem valida por si a futura publicação.

### 7.1 Contrato de leitura e origem

- Identificação do produto: consultar por código oficial; recuperar campos autorizados pela view `engineering` de `api-delpi GET /products/{code}?view=engineering` e os vínculos oficiais por `GET /products/{code}/suppliers?view=engineering`; expor à UI **somente através da Engineering API**.
- Valor de referência exibido = **valor oficial efetivamente retornado** pelo TOTVS, não valor do formulário, snapshot de solicitação anterior, fixture ou valor presumido. Apresentar também origem `TOTVS`, momento `consultadoEm` (timestamp da resposta de leitura efetiva, não alegar instante de alteração no ERP), e estado da leitura. Validade/freshness de snapshot requer política do owner da integração.
- Diferenciar três fatos: **valor oficial atual**, **valor proposto** e **última revisão técnica Engenharia**. A revisão-base continua automática no backend e não é campo para o usuário preencher.
- Conferir se a projeção oficial contém cada atributo; campo ausente deve exibir `Não disponível na consulta oficial`, nunca `—` entendido como vazio ou `0` arbitrário. `null` e vazio legítimo devem ter semântica diferenciada quando crítica.
- Chamada autenticada, backend AuthZ `engineering.access`, nenhuma integração direta frontend–api-delpi, nenhum SQL em Engineering API, nenhum write TOTVS. Contrato aditivo, com erros/limites/cache e compatibilidade REST/EVA explicitados.

### 7.2 Wireframe UPDATE por campo individual

```text
ALTERAÇÃO DO PRODUTO [código oficial]      Fonte: TOTVS · Consultado em 08/11/2026 10:30*
[Atualizar dados oficiais]  [indicador de leitura válida/indisponível]

CAMPO                  VALOR ATUAL NO TOTVS                   NOVO VALOR                      AÇÃO
Descrição              CHICOTE ELÉTRICO SENSOR ...            [Não alterar             ]      [Editar]
Grupo                  8001 — Componentes ...                 [Não alterar             ]      [Editar]
Tipo                   PA — Produto acabado                    [Não alterar             ]      [Editar]
Unidade                MI — Metro ...                          [Não alterar             ]      [Editar]
Conta contábil         11401006 — ...                          [Conta oficial: escolher ]      [Editar]

Ao ativar um campo:
  [✓] Alterar Conta contábil
  Atual no TOTVS: 11401006 — [descrição oficial se fornecida]
  Novo valor: [Select pesquisável do catálogo oficial]
  Justificativa: [................................]
  [Descartar mudança] [Adicionar mudança à solicitação]
```

*O timestamp é ilustrativo; no sistema usar o horário real da consulta autenticada. Nunca inferir descrição, conta ou classificação ausentes da API.

- Na abertura da tela UPDATE: exibir `loading` até carregar leitura oficial; 404 produto não encontrado; 401/403 sem acesso; 503 origem indisponível + retry; erro de campo individual = não editável sem contexto confiável, salvo exceção formal do owner.
- Campos não selecionados continuam **read-only** e **não** entram no change set. Somente `path + proposedValue + reason` do campo selecionado, com `before` capturado no snapshot governado para a auditoria; nunca transportar valores oficiais como mudanças para todos os paths.
- Mostre o valor atual mesmo ao editar, com contraste explícito `Atual (TOTVS)` x `Novo valor proposto`. Prefill do novo valor só para facilitar escolha, mas não marcar mudança se valor não foi modificado; nenhuma mudança silenciosa ao navegar.
- Se dado oficial mudar enquanto o usuário prepara a solicitação, o backend deve detectar mudança relevante no read-back/concorrência, sinalizar conflito, preservar draft, exigir reavaliação/justificativa; não rebase silencioso de alteração já solicitada.

### 7.3 Wireframe UPDATE de amarração específica SA5

```text
VÍNCULOS OFICIAIS DO PRODUTO (SA5)      Fonte TOTVS · Consultado em [horário]
[+ Adicionar vínculo]      [Atualizar vínculo selecionado]

[⌕] CÓDIGO LOJA  RAZÃO SOCIAL           PN ATUAL       CATÁLOGO ATUAL    AÇÃO
[⌕] 000089 01    WEG ...                (vazio)        CAT-001          [Editar vínculo]
[⌕] 001572 01    3RHO ...               PN-A           CAT-002          [Editar vínculo]

Editar vínculo 000089/01:
  [ ] Alterar Part Number      Atual TOTVS: (vazio)     Novo: [................]
  [ ] Alterar Catálogo         Atual TOTVS: CAT-001     Novo: [................]
  Justificativa desta operação: [.............................................]
  [Cancelar]                                            [Aplicar à solicitação]

Resumo: UPDATE do vínculo 000089/01, somente partNumber (vazio → X)
Os demais vínculos permanecem inalterados.
```

- Consulta SA5 identifica o vínculo pela chave oficial validada, não pelo índice da linha ou razão social. Só itens existentes permitem `update`; `add` seleciona SA2 oficial e propõe uma **nova** amarração, sem sobrescrever outras.
- Campos atuais de fornecedor/loja/razão social/PN/catálogo precisam vir de projeção oficial, distinguindo mestre SA2 e relacionamento SA5. Se PN/catálogo não forem expostos, inventariar e estender **api-delpi no owner correto** antes de prometer essa comparação.
- **Part Number vazio é legítimo**. Limpar explicitamente PN exige proposta de mudança, e não pode ser confundido com campo omitido (sem alteração).
- Ao editar somente PN, `catalogNumber` não entra em `fields`; ao editar somente Catálogo, `partNumber` não entra; outros vínculos nunca integram o diff.
- O backend `verify_and_complete` reconsulta os mesmos dados oficiais depois da alteração manual no ERP e verifica os paths/atributos **explicitamente propostos**. Erros ou ausência de evidência impedem publicação da revisão; capturar before/after, source e timestamp da leitura para rastreabilidade.

### 7.4 Critérios de aceite adicionais (bloqueantes)

- [ ] Um UPDATE de produto existente mostra **os valores oficiais atuais** em cada campo disponível antes de editar; nenhum usuário precisa saber a última revisão.
- [ ] O usuário altera apenas um campo SB1 e o resumo contém só esse path, justificativa e valores **antes → proposto**; demais campos não são reenviados como mudanças.
- [ ] A tabela SA5 mostra os vínculos atuais e PN/Catálogo oficiais separados; linha selecionada mostra **Atual TOTVS** vs **Novo valor**.
- [ ] Alteração de PN de um fornecedor entre N preserva todos os demais vínculos e atributos. Adição cria somente candidato para novo vínculo.
- [ ] Falhas 401/403/404/503 e atributos não verificáveis têm estado honesto, retry quando adequado e **fail-closed**; jamais mostrar dados mockados como oficiais.
- [ ] Testes REST+EVA, PostgreSQL, comparação seletiva, CAS/idempotência, read-back TOTVS, browser Playwright (desktop/tablet/mobile) e screenshots antes/depois com atributos reais autorizados; sem ERP writes.
- [ ] Nenhuma publicação em produção sem aceite funcional, contrato e aprovação do owner.

**A implementação segue pendente** até inventário/contrato e aprovação dos owners requeridos. O novo requisito **faz parte obrigatória** de `ENG-PRC-D12-GRANULAR-SUPPLIER-LINK-CHANGE-CONTRACT-AND-UX`; não tratar como refinamento decorativo de UI.


## 8. Mapa de rotas, api-delpi e trilha de implementação D12

**Documento de execução obrigatório:** [MFE-PRC-D12-ROUTES-API-DELPI-IMPLEMENTATION-BLUEPRINT.md](./MFE-PRC-D12-ROUTES-API-DELPI-IMPLEMENTATION-BLUEPRINT.md). O blueprint inventaria rotas Engenharia existentes, `api-delpi GET /products/{code}?view=engineering`, `GET /products/{code}/suppliers?view=engineering` (SA5), busca SA2, catálogos oficiais, e define **TARGET**, não PROVEN: `GET /reference-data/products/{officialCode}/edit-context` (BFF somente leitura) + extensão versionada de `POST /intake/requests` e `PATCH /requests/{id}/draft` com operações individuais `supplierLinkChanges[]`. Reutilizar `verify-and-complete` com comparação seletiva, sem criar escrita ERP. **O owner deve fechar contrato/schema/freshness/completude SA5 antes de implementação produtiva.**


## 9. Decisão PO complementar — UPDATE in-place e diffs automáticos (D13)

**Documento normativo:** [MFE-PRC-D13-DIRECT-EDIT-AUTOMATIC-DIFF-AND-SA5-OPERATIONS.md](./MFE-PRC-D13-DIRECT-EDIT-AUTOMATIC-DIFF-AND-SA5-OPERATIONS.md). O PO substituiu a escolha manual por checkbox e a edição em campo alternativo: **o valor atual do TOTVS já preenche o próprio controle**, e a aplicação detecta automaticamente mudanças por campo e amarração SA5. Diff automático classifica `update`, `add` e `remove` solicitado; mostra antes→depois, justificativas apenas para mudanças reais e desfazer. O fluxo de exclusão oficial NÃO foi autorizado: `remove` aqui é **proposta governada**, condicionada a baseline de presença/read-back de ausência pelo owner correto, sem chamada DELETE ao ERP. **Corrigir primeiro o P0 de SA5-only verify**: se o intake tem somente `supplierLinkChanges`, a verificação não pode produzir expected paths vazios nem publicar revisão sem comparação. A visão antiga de checkboxes deste arquivo representa histórico e está supersedida por D13 para UPDATE. `IMPLEMENTATION_PENDING / PRODUCTION_DEPLOY_SUSPENDED`.


## 10. D14 — Ajuste PO: justificativa por campo opcional, até 250, e pesquisa oficial colapsável

Documento normativo [D14](./MFE-PRC-D14-COMPLETE-SUPPLIER-LOOKUP-AND-OPTIONAL-REASONS.md). Depois do D13, a tela usa edicao direta e diffs; **a justificativa não deve ocupar espaço permanentemente** e não é requisito para enviar alteração autorizada. Para **todos os campos SB1** e para **cada PN/Catálogo de cada vínculo SA5** utilizar botão expansível individual com textarea multi-linha de até 250, contador, recolher/apagar. Inclusão e remoção candidata também têm razões próprias (regra de remoção owner pendente). Backend valida optional/250 e preserva auditoria; não usar supplierReason único. A busca oficial SA2 deve ser por botão lupa em coluna específica, input colapsável por linha, sem duplicar código/loja/razão. O texto histórico do REF-012 sobre justificativas obrigatórias é substituído pela decisão PO D14 para as operações liberadas; nenhum owner/authority alterado.
