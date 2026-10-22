# Suppliers F5 — Consulta CNPJ e enriquecimento cadastral estruturado

**Decisão do Product Owner:** 2026-10-20. **Estado:** `AUTHORIZED_FOR_CONTRACT_AND_READ_ONLY_DISCOVERY` / `PLANNED_IMPLEMENTATION`. Esta decisão é uma evolução das páginas existentes de Fornecedores; **não autoriza ativar CREATE/UPDATE do Protheus em produção**, nem altera automaticamente a fila E10–E14.

## 1. Objetivo funcional

Reduzir digitação e melhorar qualidade cadastral ao pesquisar um CNPJ em fontes externas com **campos estruturados**, comparar os resultados com o cadastro vigente no Protheus e permitir aplicar **sugestões selecionadas** aos formulários já existentes de criação e edição.

**IA/LLM NÃO é requisito do P0.** Usar mapeamento determinístico de campos, normalização e regras rastreáveis. Não incluir LLM apenas para comparar dois registros estruturados. Proposta futura de IA somente após demonstrar necessidade não resolvida pela comparação convencional, com decisão independente de privacidade, custo e auditabilidade.

## 2. Fluxos de usuário

### Novo fornecedor
1. Usuário informa CNPJ e aciona **Consultar CNPJ**; consulta externa é sempre explícita.
2. BFF valida CNPJ e autorização; adapter consulta fonte aprovada e retorna informações com proveniência.
3. Tela apresenta os dados sugeridos, a fonte e data/hora de consulta; permite selecionar cada campo.
4. Ao aplicar, preenche **rascunho local** do formulário compartilhado `SUPPLIER_FIELD_REGISTRY` (sem POST automático).
5. Usuário revisa campos obrigatórios, campos exclusivos do ERP, mudanças e confirma o POST somente quando o respectivo gate de escrita estiver autorizado.

### Fornecedor existente
1. Abre ficha e aciona **Consultar CNPJ** do identificador já registrado; não muda `tax_id`.
2. Compara, lado a lado, **valor Protheus** versus **valor externo**, com rótulos igual/diferente/ausente/não comparável.
3. Pode aceitar/rejeitar sugestões **campo a campo**. Campos sem PUT aprovado, campos de sistema, dados não equivalentes e CNPJ/CPF ficam somente leitura.
4. Aplicar sugestões modifica apenas o rascunho do MFE; revisão de diff e confirmação permanecem obrigatórias antes do PUT.
5. Resultado `acknowledged` não equivale a persistência; conservar conferência posterior por GET e tratamento de timeout indeterminado.

## 3. Fontes de dados — decisão de governança

**Preferir informações oficiais brasileiras de cadastro CNPJ**, desde que haja **mecanismo de acesso permitido e compatível** com a DELPI. O caráter público do cadastro **não implica que toda API governamental esteja aberta a acesso privado**, nem dispensa observância da LGPD, regras de acesso, licenciamento, rate limits, políticas de cache e origem da atualização.

A seleção concreta do provider é `TO_INVENTORY`, não presumir aprovação de Receita Federal/Conecta GOV.BR ou BrasilAPI. Avaliar:
- fonte primária e cadeia de proveniência (fonte oficial ou republicador);
- autorização de uso/acesso e termos, limites, SLA, custos e retenção;
- cobertura/latência, campos disponíveis, formatos, atualização e disponibilidade;
- exigência de chave/credencial, LGPD e observabilidade;
- circuit breaker, timeout, rate limit e resposta de indisponibilidade.

**Sem scraping informal** ou segredo no frontend. Não persistir cópia integral do cadastro externo sem finalidade, contrato e política de retenção aprovados.

## 4. Ownership / arquitetura

```text
plugins/supplies (UX, diffs, aplicação seletiva ao rascunho)
    → supplies-api (AuthZ Core-first; orchestration, fonte externa, DTO e minimização)
         → SupplierRegistryProviderPort → adapter externo aprovado
         → api-delpi (dados canônicos TOTVS, via S2S individual quando necessário)
    → POST/PUT existentes somente após revisão e feature gates do Protheus
```

- **Keycloak**: SSO/identidade; **Core**: efetivas `supplies.access`, escopo e auditoria de plataforma.
- **supplies-api**: contrato de enriquecimento, authZ server-side, validação CNPJ, ports/adapters, seleção de dados retornados, observabilidade; **não** gravar estado TOTVS em seu Postgres.
- **api-delpi**: exclusivamente integração Protheus, SQL canônico e REST existente; evitar colocar um provider CNPJ externo nela por conveniência.
- **plugins/supplies**: UI com `@delpi/plugin-ui`, `SUPPLIER_FIELD_REGISTRY` reutilizado; jamais chamar provider externo diretamente.
- **Protheus**: autoridade final do cadastro persistido; dados externos são sugestões.

## 5. Contratos candidatos (não implementados)

### Consulta estruturada
`GET /suppliers/cnpj-lookup?cnpj=<14_digitos>` na `supplies-api` — **rota ilustrativa**; verificar convenções/colisões no HEAD antes de congelar. Separar da rota dinâmica `/suppliers/{code}/{store}`. Requer `supplies.access` Core-first, validação de CNPJ e throttling por usuário/serviço. Respostas esperadas:
- 200 com `source`, `consulted_at`, `source_updated_at` (quando disponível), `cnpj` mascarado conforme política, `fields` normalizados, `missing_fields`, `field_provenance`, e `warnings`;
- 400/422 documento inválido; 404 não localizado; 429 limite; 502/503 fonte indisponível; 403 acesso ausente;
- nenhum retorno de credenciais, payload integral de terceiros ou dados não contratados.

### Comparação
Função determinística/composable para `compare(current_supplier, external_fields, field_registry)` que emite, para cada campo mapeável: `current`, `suggested`, `status`, `source`, `editable`, `reason`, normalização aplicada. Somente valores autorizados pela projeção da BFF.

Regras:
- comparação sem inferir equivalência inexistente (ex.: atividade CNAE **não** define natureza financeira, conta contábil ou condição de pagamento);
- endereço, município/UF, CEP, razão social/fantasia mapeados somente após confirmação de semântica e suporte;
- **CNPJ/CPF imutável no PUT**, código e loja imutáveis, `codusr` resolvido no Core;
- dados de CPF/pessoa física, contatos de pessoa natural e sócios sujeitos a minimização LGPD;
- valores externos vazios **não limpam** cadastro Protheus;
- sugestão desatualizada, ambígua ou não equivalível é informativa, nunca aplicada automaticamente;
- uma sugestão só entra no diff caso usuário a selecione e o campo possua capacidade permitida no POST/PUT do contrato vigente;
- a seleção não contorna feature gates nem a homologação REST.

## 6. UI/Help e acessibilidade

Ação **Consultar CNPJ** em criação e detalhe; painel/área de comparação com valor Protheus, valor externo, indicador de divergência, origem e data; checkboxes por campo; botões **Aplicar selecionados ao formulário** e **Cancelar**, sem gravar ao clicar em aplicar. Estados loading, empty, no-match, partial, error, 403, 429, provider indisponível, offline; teclado, foco, mobile, claro/escuro, Help sincronizada.

Usar o kit `@delpi/plugin-ui`, reaproveitar a estrutura de 5 seções e `SUPPLIER_FIELD_REGISTRY`; CSS local isolado em `.dashboard-supplies-portal`.

## 7. Entrega em fatias (F5)

- **F5.P0 Discovery/Contract:** selecionar/comprovar provider(s), termos, limites, campos, ownership, LGPD, contratos de erro e matriz de equivalência CNPJ→registry. Aprovação explícita de fonte antes de requests produtivos.
- **F5.S1 Backend read-only:** port+adapter na supplies-api, endpoints tipados, cache/timeouts/circuit breaker apropriados, rate limit, AuthZ, contrato de proveniência, mocks e testes de fornecedor ausente/indisponível. Sem modificar POST/PUT.
- **F5.S2 MFE compare/apply draft:** consulta por CNPJ, diff determinístico, seleção campo a campo, aplicar ao rascunho, Help e testes UI. **Zero gravação automática**.
- **F5.S3 Runtime acceptance:** testes positive/sibling/negative, acessibilidade, smoke federado e documentação de evidências; indisponibilidade de provider não impede consulta do Protheus.
- **F5.S4 opcional IA/LLM:** somente se necessidade comprovada, novo contrato e decisão formal. Não é pré-requisito.

## 8. RQ/AC candidatos (identificadores finais a reconciliar)
- F5-RQ-01: consultar CNPJ válido por fonte aprovada; AC dados estruturados + proveniência, erro seguro e sem persistir.
- F5-RQ-02: comparação dos campos equivalentes; AC iguais/diferentes/ausentes exibidos, sem comparação de campos não equivalíveis.
- F5-RQ-03: aplicar sugestões escolhidas ao rascunho; AC nenhum POST/PUT disparado nessa ação.
- F5-RQ-04: LGPD e direitos de acesso; AC documento mascarado onde requerido, usuário não autorizado recebe 403, nenhum segredo exposto.
- F5-RQ-05: segurança contra substituição indevida; AC campos bloqueados/ERP-only não são alterados e dados vazios externos não limpam valores.
- F5-RQ-06: robustez; AC 404, 429, timeout, provider down, cache, sibling e ausência de retry de escrita.
- F5-RQ-07: kit-first, Help, mobile, foco, tema e URL; AC testes e smoke real antes de PASS.

## 9. Dependências e não-objetivos

**Frente em paralelo a Gabriel:** validação do REST produtivo sobre `DELPI`, contrato POST de retorno de `A2_COD/A2_LOJA`, required fields e campos PUT homologados. A dependência **não bloqueia o enriquecimento read-only**, mas **bloqueia ativar persistência produtiva**.

Sem LLM, sem busca por CPF, sem dados bancários extraídos de fonte pública, sem scraping, sem automação de gravação, sem criação de permission por botão, sem substituir os campos internos do ERP por dados públicos e sem abrir conexão do MFE à fonte externa.

**Status:** `PLANNED` (funcionalidade aprovada como evolução; implementação não executada neste documento). Próximo passo: brief Cursor F5.P0 sobre fornecedores de dados estruturados e matriz de campos, separado de F4/Gabriel.
