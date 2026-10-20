# Roadmap — Gestão cadastral de fornecedores no Portal Suprimentos

> **Estado:** TARGET / PLANNED (2026-10-20). Documento de evolução, **não** autorização de execução ou escrita no ERP. Respeitar a fila canônica E13/WF-09 (lista) → E14/WF-10 (ficha Supplier 360) do `IMPLEMENTATION-PLAN.md`; não promover etapas nem sobrepor o foco E10 sem decisão explícita.
>
> **Reancoragem:** consultar HEAD remoto, Project Instructions, `.cursor`, authorities/ADRs, código, contratos, testes e ledger antes de planejar ou implementar. Documento de roadmap não comprova runtime.

## 1. Visão e fronteiras

Criar uma jornada integrada para **listar/pesquisar, consultar, cadastrar, editar um campo ou vários campos de uma vez e conferir o resultado** no cadastro de fornecedor Protheus. A mesma experiência permitirá homologação assistida de GET/POST/PUT quando autorizada. Evolução posterior: pesquisar pelo CNPJ em fonte externa, comparar campos encontrados e **sugerir** preenchimento — nunca gravar automaticamente.

**Owner de experiência:** `plugins/supplies` (MFE existente, `/apps/supplies`); **BFF de produto:** `supplies-api` (confirmar inventário e contratos); **adapter TOTVS e regras de integração:** `api-delpi`; **identidade, RBAC e grants:** Core API; **runtime de negócio:** Protheus MATA020. O MFE não deverá acessar banco, Core S2S ou TOTVS diretamente, nem substituir autorização backend por estado UI.

A rota `/apps/supplies/suppliers` já consta do manifesto `plugins/supplies/supplies.manifest.json`, como rota não exposta no menu. `/apps/supplies/suppliers/:code/:store` é ficha reservada pelo `DIRECTORY-OBJECTS.md`; não ativar antes da implementação. Reusar `SuppliesSupplierIdentity` e `EntityAvatarLabel` em listas e ficha, sem clonar estilos.

## 2. Estado comprovado e gaps

| Capacidade | Estado de base | Dependência |
|---|---|---|
| GET fornecedor por ID de oito dígitos | PROVEN no código `api-delpi` | Expor via BFF contratual ao MFE, após inventário |
| POST inclusão | PROVEN no código com gate default OFF | Autorização, `codusr`, runtime live e postcondition pendentes |
| PUT alteração | PROVEN no código com gate default OFF | Contrato comprovado somente para `supplier_name` e `supplier_short_name` |
| Busca por nome/CNPJ e lista paginada | TO_INVENTORY, sem contrato de listagem REST comprovado | Descobrir equivalente canônico; contrato read-only paginado antes da UI |
| Edição de todos os campos | TARGET, **não suportada pelo PUT atual** | Evidência de editabilidade upstream e validações por campo/empresa |
| Busca/preenchimento por CNPJ via internet | FUTURE/TARGET, sem provider aprovado | Contrato de consulta externa, LGPD, rate limit, dados/proveniência |
| Deploy recente informado pelo usuário | REPORTED, não verificado por esta documentação | Revalidar SHA e flags do runtime antes de testes reais |

## 3. Jornada funcional e páginas

### E13 / WF-09 — Consulta e lista de fornecedores

- Cabeçalho consistente com Portal Suprimentos; ação **Novo fornecedor** somente com permissão efetiva e gate operacional.
- Filtros persistidos na URL: código+loja, razão social/nome fantasia e CNPJ; empresa/filial somente onde o contrato suportar. Busca por nome/CNPJ fica **não disponível** até ter backend real.
- Tabela paginada, ordenação e estados de carregamento, vazio, erro e resultados; sem carregar SA2 inteira ou usar busca ilimitada.
- Colunas candidatas: código+loja, razão social, fantasia, documento mascarado quando aplicável, cidade/UF e estado de cadastro **somente se publicados pelo backend**.
- Ações abrir ficha e atualizar consulta; deep link estável, filtros preservados e feedback de erro.
- Na primeira entrega sem backend de listagem, permitir **consulta por ID** com ficha e estado explicativo em vez de simular lista completa.

### E14 / WF-10 — Ficha de fornecedor e gestão cadastral

- Identidade (código+loja, nome), origem e última consulta real quando disponíveis.
- Seções: **Identificação**, **Endereço**, **Contato**, **Fiscal**, **Financeiro/Compras**, com organização responsiva, labels com help contextual e leitura acessível.
- Modo leitura, editar e cancelar; mudanças agrupadas em um **diff de campos** antes de salvar; editar um campo ou múltiplos campos no mesmo PUT.
- Campos não editáveis claramente apresentados como consulta; sem affordance falsa de edição para atributos fora da allowlist. Hoje somente razão social e fantasia estão habilitáveis no PUT, sujeito a gate e permissão.
- Criação por POST com formulários por seção, campos e dependências conforme matriz REST→SA2, sem declarar obrigatoriedade não confirmada; validação, prévia e confirmação explícita.
- Após POST/PUT, mostrar **acknowledged ≠ persistência comprovada**; quando houver ID confiável, consultar GET e exibir diferenças entre enviado/retornado; timeout e outcome indeterminado não levam a retry automático.
- Proteção contra perda de alterações não salvas, ação de cancelar e fallback para consulta sem escrita.
- Modal/drawer apenas para tarefas focais; ficha completa usa rota própria e suporte mobile.

## 4. Política de componentes — `@delpi/plugin-ui` primeiro

**Regra vinculante:** toda interação visual genérica, chrome, estilos de componentes e acessibilidade reutilizáveis devem residir em `plugins/plugin-ui` e ser importados via **Module Federation** (`@delpi/plugin-ui`) pelo `plugins/supplies`. **O MFE não poderá duplicar nem copiar o CSS do kit**; CSS local apenas layout de página e tokens `--delpi-ui-*`.

| Necessidade na tela | Candidato já catalogado em plugin-ui | Owner da lógica de negócio |
|---|---|---|
| Estrutura e cabeçalho | `PageHero`, `TopBar`, `BackLink` | supplies MFE |
| Tabela e paginação | `DataTable`, `DataTableSection`, `CompactPagination` | BFF: consulta/filtros; MFE: estado e composição |
| Busca e filtros | `CatalogSearchBar`, `SelectField`, `ClearFiltersButton` | supplies MFE + BFF |
| Ações de criar/editar/salvar | `ActionButton`, `IconButton` | supplies MFE, authZ final no backend |
| Formulários e ajuda | `FieldLabel`, `HelpTooltip`, `SectionHintLabel`, `SelectField` | Conteúdo pt-BR e validação de domínio no consumidor/contrato |
| Estados | `ScreenLoading`, `InlineLoadingProgress`, `EmptyState`, `EmptyGuidance`, `AlertQueue` | supplies MFE |
| Confirmação de escrita | `ModalShell`, `DrawerShell` | supplies MFE; não criar modal duplicado |
| Identidade visual fornecedor | `EntityAvatarLabel`, `createDashboardEntityAvatarLabel` | `SuppliesSupplierIdentity` existente |
| Exportação futura, se fizer sentido | `TabularExportButtons` | Somente dados autorizados/contrato real |

**Inventário obrigatório em HEAD**: verificar exports exatos, API de props, catálogo `plugins/plugin-ui/docs/component-catalog.md`, demos, consumo real pelo supplies e regras `.cursor/rules/plugins-reusable-components.mdc`. A tabela indica **candidatos documentados**, não obriga uso inadequado.

### Componentes compartilhados novos — apenas quando faltar equivalente

Potenciais necessidades transversais (inventariar antes): `EditableField` para leitura/edição por campo, `FieldChangeReview` para comparação antes de salvar, `FormSection` para agrupamento responsivo, `OutcomeStatus` para ACK/confirmado/indeterminado e `ProvenanceBadge` para dados sugeridos por fonte externa.

**Não criar por padrão.** Para cada proposta registrar `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY` e `REUSE_DECISION=REUSE|EXTEND|NEW`, owner/consumidores reais, contrato público de props, a11y, CSS/tokens, catálogo/demo, testes e custo de manutenção. Componentes com nomes ou regras de fornecedor **não pertencem ao kit genérico**; ficam no `plugins/supplies` (ou no owner legitimado).

## 5. Contratos/gates backend-first

1. Descobrir consulta paginada existente na `supplies-api`/`api-delpi` ou serviços legítimos; se inexistente, especificar GET read-only paginado com limites, filtros e RBAC, antes de prometer busca por nome/CNPJ.
2. Expor na `supplies-api` a composição para lista/detalhe/criação/atualização segundo os boundaries; não fazer MFE→api-delpi direto sem decisão arquitetural explícita.
3. Preservar permissões distintas read/create/update, feature gates independentes e retorno seguro 401/403/503. Nunca confiar em UI/JWT/headers do cliente como autorização final.
4. Evolução de PUT além de `supplier_name`/`supplier_short_name`: **depende** de prova upstream de editabilidade, omissão, limpeza explícita, atomicidade, concorrência e diferenças por empresa. O SX3 não prova editabilidade REST.
5. `codusr` obtido do Core pelo backend; equivalência com `USR_ID` e formato de sucesso persistem lacunas; POST/PUT sem retry automático; não inferir código criado nem sucesso de negócio de 2xx.
6. Observar LGPD, minimização de dados pessoais, auditoria, logs redigidos, tratamento de falhas e rollback/compensação.

## 6. Evolução futura: CNPJ assistido

Fluxo alvo: digitar CNPJ → consultar serviço externo de dados cadastrais autorizado → mostrar fonte, momento, confiabilidade e diferenças com dados atuais → permitir aceitar/rejeitar **por campo** ou aplicar alterações selecionadas → revisar diff final → salvar por POST/PUT com confirmação explícita e validação final Protheus.

O dado externo é **sugestão**, não autoridade. Não usar scraping, provider, chave ou serviço novo sem inventário, aprovação de owner, contrato, tratamento de limites/LGPD e política de retenção. As integrações devem residir no boundary backend autorizado, nunca com segredo no MFE.

## 7. Fases e critérios de aceite de roadmap

- **Fase de descoberta**: reanchor, inventário real da tela placeholder, plugin-ui e API, owners/consumers, conflitos e gates da fila E13/E14; produzir RQ/AC seguindo IDs vigentes.
- **Contrato de listagem**: GET paginado e pesquisa com evidência, filtros tipados e negativas RBAC. Não criar lista fake.
- **Composição frontend E13**: rota/lista/consulta por ID, componentes do kit importados por remote, loading/empty/error, URL/deep link, testes e evidência visual.
- **Ficha E14**: detalhe por código/loja, seções, edição individual e múltipla **somente dos campos permitidos**, criação assistida por POST com gate e diff/confirm; testes sem escrita real.
- **Ampliação do PUT**: gate contratual separado antes de tornar demais campos editáveis; testes automatizados e homologação live controlada em entrega distinta.
- **CNPJ externo (futuro)**: proposta e integração contratual independente com revisão humana.

**AC candidatos (não criar IDs canônicos paralelos):** kit-first e consumo federado; nenhuma duplicação de UI; lista lastreada em GET real; ficha abre por deep link; RBAC por operação; campos não homologados read-only; diff antes de escrita; zero secrets; resultados técnicos separados de outcome; testes unit/integration/UI e gate visual; documentação/ledger atualizados; main verificada quando execução for autorizada.

## 8. Referências

- [Roadmap principal de Suprimentos](./README.md)
- [Fila executável vigente](./IMPLEMENTATION-PLAN.md)
- [Diretório de fornecedor e pessoa](./DIRECTORY-OBJECTS.md)
- [Plano de interface transversal](../../../api-delpi/docs/integrations/protheus-supplier-management-ui-plan.md)
- [Contrato REST fornecedores](../../../api-delpi/docs/integrations/protheus-rest-supplier-api-contract.md)
- [Matriz REST→SA2](../../../api-delpi/docs/integrations/protheus-rest-supplier-post-field-matrix.md)
- [Catálogo de componentes do plugin-ui](../../../plugins/plugin-ui/docs/component-catalog.md)
- [Playbook páginas MFE](../../05-plugin-system/playbook-mfe-page-excellence.md)

**Resultado:** backlog detalhado, não implementação. Atualizar este arquivo e as authorities/ledger aplicáveis quando o estado mudar; não promover fase ou declarar deploy sem evidência.
