# Gestão cadastral de fornecedores — autorização de frente prioritária (20/10/2026)

> **Decisão expressa do Product Owner nesta conversa:** retomar imediatamente a frente específica de **consulta, cadastro e alteração de fornecedores**, conectando os contratos existentes de Protheus ao BFF `supplies-api` e construindo a experiência `plugins/supplies`. Não continuar apenas produzindo planos. Esta é uma **autorização de preparação e implementação incremental dessa frente**, sujeita aos gates técnicos abaixo. **Não equivale a autorização de escrita real no Protheus, ativação dos feature flags, deploy produtivo ou cutover**.
>
> **Mudança controlada de prioridade / exceção de sequenciamento:** o planejamento canônico ainda registra E10 como `INCONCLUSIVE` e E11/E12/E13/E14 dependentes. Esta decisão **não altera retroativamente nem declara concluídos os gates**. Deve ser reconciliada formalmente pela coordenação/PO com o `IMPLEMENTATION-PLAN.md` antes de declarar E13/E14 promovidos ou alterar a fila geral. Implementação preparatória e testes locais ficam autorizados; promoção operacional permanece bloqueada até a reconciliação.

## Resultado de produto desejado

Página de **Fornecedores** no Portal Suprimentos com lista paginada, busca, ficha individual, formulário de novo fornecedor e edição de campos efetivamente suportados. Fluxo `plugins/supplies → supplies-api → api-delpi → Protheus`. UI sempre pela BFF; autenticação S2S individual com Keycloak; `supplies.access` do Core como autorização funcional operacional. `supplies.manage` permanece para administração, sem permissões CRUD adicionais.

## Baseline de evidências

- [Contract freeze P2](./SUPPLIERS-P2-CONTRACT-READINESS.md): SA2010 empresa 01; `A2_FILIAL = ''`; `supplier_id = A2_COD(6)+A2_LOJA(2)`; lista paginada ainda não implementada; GET REST por ID presente.
- [Roadmap cadastral](./FORNECEDORES-GESTAO-CADASTRAL-ROADMAP.md): UX de listagem/ficha/edição, controle de mudanças e reconciliação posterior ao GET.
- [ADR-010](./adr/ADR-010-s2s-individual-authentication.md): `DelpiS2SApiGateway` e `require_s2s_*`; não reutilizar o decorator legado de token compartilhado. Produção criptográfica reportada PASS; **rota de fornecedores e delegação usuário→Protheus ainda não provadas ponta a ponta**.
- Rotas `api-delpi` reportadas: `GET /integrations/protheus/suppliers/{supplier_id}`, `POST /integrations/protheus/suppliers`, `PUT /integrations/protheus/suppliers/{supplier_id}`. POST/PUT preservam feature gates OFF e autorização técnica atual. Revalidar código e contratos no HEAD antes do diff.
- PUT permite somente `supplier_name` e `supplier_short_name` conforme allowlist comprovada. Criação depende de matriz REST→SA2 e obrigatoriedade validada pelo owner TOTVS. `codusr` deriva exclusivamente do Core. HTTP 2xx = ACK, não prova persistência.

## Entregas incrementais e critérios de parada

### S1 — api-delpi: lista paginada / adapter de leitura

Implementar `GET /supplies/suppliers` conforme P2, com extensão não breaking do `TotvsSupplierRepository`, envelope `paged_list`, allowlists de filtro/sort, isolamento da empresa 01 e testes de consumidores irmãos. Autenticação individual S2S restrita à identidade `supplies-api` e escopo mínimo. Resolver contrato de chamadas diretas sem criar permission por CRUD.

### S2 — supplies-api: BFF de leitura e escrita protegida

Implementar `GET /suppliers`, `GET /suppliers/{code}/{store}`; adicionar `POST /suppliers` e `PUT /suppliers/{code}/{store}` com DTOs restritos, AuthZ Core-first (`supplies.access`), identidade de ator delegada, gateway S2S e tratamento de erros. Se os POST/PUT upstream não aceitarem o S2S individual com ator validado, tratar como **dependência de contrato**: não rebaixar para token legado/superadmin nem contornar decorators. BFF não altera gates Protheus e não faz retry automático de escrita.

### S3 — plugins/supplies: UX de fornecedores

Reutilizar `@delpi/plugin-ui` por Module Federation. Construir lista, filtros, paginação e ficha com URL/deep-link; criar formulário de inclusão e edição somente dos campos homologáveis. Formulário de edição deve permitir modificar um ou dois nomes juntos, revisar diferenças, cancelar, proteger mudanças não salvas. Ações de escrita devem ficar desabilitadas e com explicação quando gates/contratos estiverem fechados, sem simular sucesso. Estados loading, empty, partial, error, 403, 404; mobile, claro/escuro, teclado/foco, Help sincronizada.

### S4 — testes, homologação e runtime

Testes positivos, sibling e negativos em cada owner; validação de CPF/CNPJ e política de mascaramento no **BFF** antes de publicar dados pessoais desnecessários no navegador; testes de AuthZ, token legado rejeitado, usuario sem acesso e cliente S2S errado; POST/PUT com upstream simulado e gate OFF. Build e smoke federado autorizados. Escrita real Protheus requer aprovação específica do PO + owner TOTVS, identidade `codusr` verificada, campos obrigatórios, resultado de POST/PUT e método de consulta pós-escrita comprovados. Timeout de escrita gera resultado indeterminado; nunca retry automático.

## Pendências de decisão (não reconciliar silenciosamente)

1. **Fila E10→E13/E14:** autorização de frente prioritária não elimina dependências documentadas; solicitar reconciliação formal do roadmap antes da promoção.
2. **LGPD:** P2 fala em mascarar `tax_id` apenas na UI. Preferir projeção segura no BFF para lista; inventariar necessidade de exibição íntegra e homologar com owner.
3. **Operação direta api-delpi:** confirmar permissões existentes para chamadas não-S2S, sem criar permission arbitrária.
4. **Escopos Keycloak:** `suppliers.read`, `suppliers.create`, `suppliers.update` são candidatos técnicos; confirmar claim e provisionamento autorizado.
5. **Escrita:** habilitação de flags, identidade Core↔Protheus, criação de `A2_COD`, shape real de sucesso, idempotência/timeout e homologação TOTVS exigem gate específico.

## Report obrigatório do Cursor

`BASE HEAD`, `ORIGIN MAIN`, `FINAL HEAD`, `GIT STATUS`, `RQ/AC`, `AUTHORITIES`, `OWNERS`, `CONTRACT IMPACT`, `FACTS PROVEN`, `TO_INVENTORY`, `EXECUTION_DRIFT`, `FILES INSPECTED/CHANGED`, `SECURITY`, `TESTS`, `POSITIVE/SIBLING/NEGATIVE`, `HELP`, `RUNTIME`, `OUTCOME`, `RESIDUAL SEARCH`, `UNRESOLVED`, `NEXT STEP`.

Esta decisão documenta a retomada de desenvolvimento; **nenhuma rota de fornecedores, tela, flag ou escrita produtiva é afirmada como implementada neste documento**.
