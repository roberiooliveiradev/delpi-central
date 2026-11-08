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
