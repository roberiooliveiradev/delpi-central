# Plano transversal — tela de gestão/homologação de fornecedores Protheus

**Data:** 2026-10-20. **Estado:** PLANNED / inventário de frontend e consumidores pendente. **Não equivale a autorização de escrita em produção.**

## Objetivo solicitado

Disponibilizar interface para consultar fornecedores, criar via POST e alterar campos individualmente ou em conjunto via PUT. A tela serve inicialmente como diagnóstico e homologação assistida. Evolução futura: informar CNPJ, consultar serviço externo autorizado e propor preenchimento/atualização dos dados mediante revisão humana.

## Estado comprovado no backend

- `GET /integrations/protheus/suppliers/{supplier_id}`: busca por chave de oito dígitos (código+loja), **não é endpoint de listagem**.
- `POST /integrations/protheus/suppliers`: inclusão implementada, feature gate separado default off; homologação de escrita real pendente.
- `PUT /integrations/protheus/suppliers/{supplier_id}`: atualização implementada, feature gate separado default off; allowlist atualmente restrita a `supplier_name` e `supplier_short_name`; homologação real pendente.
- `codusr`: resolvido via Core para o ator autenticado, equivalência com `USR_ID` ainda TO_INVENTORY.
- Hardening (gate antes de Core/OAuth/upstream) reportado integrado; user informou deploy realizado, **SHA do runtime ainda não verificado nesta interação**.

## Gaps de contrato antes da promessa de UX

1. **Listagem real com pesquisa/paginação:** encontrar capability equivalente no owner legítimo, sem assumir que GET por ID lista todos; se ausente, desenhar contrato backend-first para pesquisa por nome/CNPJ e filtros, com restrições de volume, AuthZ e observabilidade. SQL read-only pode ser adapter autorizado apenas quando aprovado como contrato de consulta, não como desvio da REST nem substituição silenciosa.
2. **PUT de todos os campos:** exigir confirmação upstream de campos editáveis, validações, semântica de omissão/null, atomicidade e concorrência; NÃO expandir allowlist baseada apenas em SX3. Suportar edição individual ou de múltiplos campos dentro de uma única transação de atualização autorizada; leitura após escrita para verificação.
3. **Frontend/host/owner:** inventariar MFE/Portal e componentes compartilhados, reutilizar UI de tabelas, formulários, feedback, permissão e loading; evitar criação de novo produto ou autoridade.
4. **Segurança:** feature gates default off e RBAC separados read/create/update, sem escrita incidental; não expor `codusr`, tokens nem segredos; status de escrita `acknowledged` != persistência comprovada.
5. **Dados por CNPJ (futuro):** integração externa é fonte auxiliar, nunca autoridade final. Pré-preenchimento com proveniência, timestamp, revisão e confirmação explícita do usuário antes de persistir, tratamento LGPD, limites e disponibilidade; não construir automaticamente nesta etapa.

## UX proposto

- Tabela compacta paginada com busca por código+loja, razão social e CNPJ **somente após contrato de pesquisa confirmado**.
- Detalhe com seções Identificação, Endereço, Contato, Fiscal e Financeiro; somente campos autorizados podem ser editados.
- Botões `Novo`, `Editar`, `Cancelar`, `Salvar alterações`; alterações individuais ou múltiplas no mesmo formulário; mostrar diff antes de enviar, confirmação explícita e resultado de conferência por GET.
- Tela de teste não substitui módulo de produção: registrar consentimento de execução, ambiente, RBAC e feature gate; evitar fornecedor fictício como dado genérico ou credencial em documentação.
- Interface futura `Consultar CNPJ` busca dados externos e sugere diferenças antes de salvar; **não executar importação automática**.

## Sequência sugerida

1. Reancoragem GitHub HEAD, instructions, owners e inventário da UI.
2. Localizar ou especificar contrato de listagem/pesquisa antes de construir tabela dinâmica.
3. Obter ratificação de edição dos demais campos pelo owner TOTVS; até lá somente nome e fantasia editáveis.
4. Implementar MFE com shared components, estados loading/empty/error, filtros e fluxo create/detail/update; feature gates e RBAC refletidos sem substituir autorização backend.
5. Testes UI/contrato sem POST/PUT reais, evidência visual e atualização de ledger.
6. Planejar homologação operacional separadamente; não inferir runtime deploy do relato sem SHA verificado.

**Referências:** `protheus-rest-supplier-api-contract.md`, `protheus-rest-supplier-post-field-matrix.md`, `protheus-rest-supplier-write-handoff.md`, playbook SA2 §44.3, ownership Core.

**Notas:** frontend específico e autoridade de pesquisa ainda TO_INVENTORY. Não alterar estruturas/campos do ERP sem contrato.
