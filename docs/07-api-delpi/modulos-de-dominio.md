# Minha DELPI — API DELPI: Módulos de Domínio

> **Arquivo:** `docs/07-api-delpi/modulos-de-dominio.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** organização de módulos de domínio dentro da `api-delpi`

---

## 1. Objetivo

Este documento descreve como módulos de domínio devem ser organizados dentro da **API DELPI**.

A API DELPI pode hospedar módulos operacionais que não pertencem à Core API, como módulos de qualidade, integrações com TOTVS e domínios próprios de plugins.

---

## 2. Conceito de módulo de domínio

Um módulo de domínio representa um conjunto funcional com regras próprias.

Exemplos:

- qualidade;
- não conformidades externas;
- produtos;
- fornecedores;
- estoque;
- compras;
- vendas;
- indicadores operacionais.

Cada módulo deve ter fronteiras claras:

- entidades próprias;
- use cases próprios;
- ports próprios;
- repositories próprios;
- rotas próprias;
- permissões próprias quando aplicável.

---

## 3. Regra arquitetural central

Módulos de domínio na `api-delpi` devem seguir Clean Architecture.

Fluxo recomendado:

```text
Route
 ↓
Composer
 ↓
UseCase
 ↓
Port
 ↓
Repository concreto
 ↓
Banco / TOTVS / Exporter / integração
```

Isso evita acoplamento entre HTTP, banco, domínio e integrações externas.

---

## 4. Camadas

### 4.1 Domain

Contém o núcleo do domínio.

Responsabilidades:

- entidades;
- value objects;
- serviços de domínio;
- ports;
- regras puras.

Não deve conhecer:

- FastAPI/Flask;
- banco;
- SQL;
- JSONResponse;
- Gateway;
- TOTVS concreto.

---

### 4.2 Application

Contém casos de uso e DTOs.

Responsabilidades:

- orquestrar regras;
- chamar ports;
- coordenar validações;
- receber DTOs de entrada;
- retornar dados de aplicação.

Não deve conhecer:

- SQL;
- framework web;
- response HTTP concreta.

---

### 4.3 Infrastructure

Contém detalhes técnicos.

Responsabilidades:

- repositories concretos;
- conexão com TOTVS;
- conexão com `postgres-plugins`;
- exporters;
- mappers;
- storage;
- integrações externas.

---

### 4.4 Interfaces

Contém bordas de entrada.

Responsabilidades:

- rotas HTTP;
- validação de parâmetros HTTP;
- chamada ao composer/use case;
- serialização da resposta;
- tradução de erros para HTTP.

---

### 4.5 Composition

Contém montagem de dependências.

Responsabilidades:

- instanciar repositories concretos;
- instanciar exporters;
- injetar dependências em use cases;
- centralizar composição de cada feature.

---

## 5. Estrutura recomendada

Estrutura geral recomendada para a `api-delpi`:

```text
app/
  domain/
    entities/
    ports/
    services/

  application/
    dto/
    use_cases/

  infrastructure/
    persistence/
      totvs/
      plugins/
    exporters/
    mappers/

  interfaces/
    http/
      routes/

  composition/
```

Para um módulo específico, manter subpastas por domínio.

Exemplo:

```text
app/
  domain/
    entities/
      external_nc/
    ports/
      external_nc/
    services/
      external_nc/

  application/
    dto/
      external_nc/
    use_cases/
      external_nc/

  infrastructure/
    persistence/
      plugins/
        repositories/
          external_nc/

  interfaces/
    http/
      routes/
        external_nc_routes.py

  composition/
    external_nc_composer.py
```

---

## 6. Módulo de qualidade — External NC

A especificação de qualidade define o módulo de não conformidades externas como:

- frontend próprio de plugin;
- backend hospedado dentro da `api-delpi`;
- persistência no `postgres-plugins`;
- governança pela Core API;
- permissões via manifesto;
- menu dinâmico via Portal.

Nome conceitual do contexto:

```text
external_nc
```

Base de API sugerida:

```text
/apps/api-delpi/quality/external-nc
```

---

## 7. Domínio de não conformidades externas

O módulo deve cobrir:

- cadastro e triagem;
- contenção;
- investigação;
- causa raiz;
- plano de ação;
- validação de eficácia;
- comentários;
- anexos;
- auditoria;
- dashboard;
- relatórios.

Esse módulo não deve ser tratado como planilha digitalizada, mas como produto corporativo com workflow próprio.

---

## 8. Entidades sugeridas para External NC

Agregados principais:

```text
ExternalNonconformity
ExternalNonconformityAction
ExternalNonconformityRootCause
ExternalNonconformityEffectivenessCheck
ExternalNonconformityAttachment
```

Entidades complementares:

```text
Supplier
NonconformityComment
NonconformityTeamMember
NonconformityAuditEvent
```

Value objects sugeridos:

```text
NonconformityCode
SeverityLevel
WorkflowStatus
ActionType
OccurrenceType
Quantity
Deadline
```

---

## 9. Workflow do módulo External NC

Status principal sugerido:

```text
draft
open
under-triage
containment-defined
under-investigation
action-plan-approved
in-progress
pending-effectiveness-check
closed
cancelled
reopened
```

Status de interação com fornecedor:

```text
not-requested
awaiting-supplier
supplier-responded
supplier-action-pending
supplier-validated
supplier-overdue
```

---

## 10. Regras obrigatórias do domínio

Regras documentadas para External NC:

- não encerrar sem validação de eficácia aprovada;
- não aprovar plano sem causa raiz registrada;
- não concluir ação sem responsável e prazo;
- permitir reabertura com justificativa;
- anexos podem existir na ocorrência, ação e validação;
- ações vencidas devem ser identificadas no dashboard;
- registrar auditoria em ações críticas.

---

## 11. Persistência de módulos

Módulos novos que não pertencem ao TOTVS devem persistir no `postgres-plugins`.

Para External NC, schema sugerido:

```text
quality
```

Tabelas sugeridas:

```text
quality.external_nc_suppliers
quality.external_nonconformities
quality.external_nc_root_causes
quality.external_nc_actions
quality.external_nc_effectiveness_checks
quality.external_nc_attachments
quality.external_nc_comments
quality.external_nc_team_members
quality.external_nc_audit_events
```

---

## 12. Integração com TOTVS

Módulos de domínio podem consultar TOTVS quando necessário, mas isso deve ser feito como integração.

Para qualidade, integrações futuras previstas:

- fornecedor;
- pedido de compra;
- nota fiscal;
- material;
- lote;
- custo.

Regra:

> TOTVS pode enriquecer o processo, mas o domínio novo não deve persistir seus dados principais no TOTVS.

---

## 13. Permissões por módulo

Módulos consumidos pelo Portal devem declarar permissões no manifesto do plugin correspondente.

Exemplo de permissões para External NC:

```text
quality.external-nc.view
quality.external-nc.create
quality.external-nc.edit
quality.external-nc.assign
quality.external-nc.comment
quality.external-nc.attach
quality.external-nc.investigate
quality.external-nc.approve-plan
quality.external-nc.execute-action
quality.external-nc.validate-effectiveness
quality.external-nc.close
quality.external-nc.reopen
quality.external-nc.export
quality.external-nc.dashboard.view
quality.external-nc.admin
```

A API DELPI deve validar permissões em endpoints sensíveis.

---

## 14. Relação com manifesto

O backend de módulo pode ser compartilhado pela `api-delpi`.

No manifesto do plugin frontend, o bloco `backend` deve apontar para a `api-delpi`, não para um serviço novo, quando essa for a decisão arquitetural.

Fluxo:

```text
Plugin frontend
  ↓
Manifesto declara backend api-delpi
  ↓
Core API registra permissões e rotas
  ↓
Portal carrega plugin
  ↓
Plugin consome api-delpi
```

---

## 15. Use cases de módulo

Cada ação relevante deve ter um use case explícito.

Para External NC, use cases mínimos sugeridos:

```text
CreateExternalNonconformityUseCase
ListExternalNonconformitiesUseCase
GetExternalNonconformityDetailsUseCase
UpdateExternalNonconformityUseCase
TransitionExternalNonconformityStatusUseCase
AddRootCauseUseCase
CreateActionUseCase
UpdateActionUseCase
CompleteActionUseCase
RegisterEffectivenessCheckUseCase
UploadAttachmentUseCase
AddCommentUseCase
ExportNonconformityReportUseCase
GetExternalNcDashboardUseCase
```

---

## 16. Ports e repositories

Cada use case deve depender de ports.

Exemplo conceitual:

```text
ExternalNonconformityRepositoryPort
ExternalNcActionRepositoryPort
ExternalNcAttachmentStoragePort
ExternalNcAuditRepositoryPort
```

Implementações concretas devem ficar em infraestrutura:

```text
app/infrastructure/persistence/plugins/repositories/external_nc/
```

Se a consulta for TOTVS, usar infraestrutura TOTVS separada:

```text
app/infrastructure/persistence/totvs/
```

---

## 17. Composer

Cada módulo deve ter composer próprio.

Exemplo:

```text
app/composition/external_nc_composer.py
```

Responsabilidade:

- instanciar repositories concretos;
- instanciar serviços auxiliares;
- montar use cases;
- centralizar dependências do módulo.

A rota não deve montar múltiplas dependências diretamente.

---

## 18. Rotas HTTP

Rotas do módulo devem ficar em arquivo próprio.

Exemplo:

```text
app/interfaces/http/routes/external_nc_routes.py
```

ou conforme padrão vigente do projeto:

```text
app/interface/http/routes/external_nc_routes.py
```

A rota deve:

- receber request;
- validar parâmetros básicos;
- chamar composer;
- chamar use case;
- devolver resposta;
- tratar erro.

Não deve:

- montar SQL;
- acessar banco diretamente;
- executar regra central de domínio.

---

## 19. Auditoria de módulo

Módulos com ações críticas devem ter auditoria própria.

Para External NC, a especificação prevê:

```text
external_nc_audit_events
```

Eventos esperados:

- criação;
- transição de status;
- inclusão de ação;
- conclusão de ação;
- validação de eficácia;
- fechamento;
- reabertura;
- upload de anexo.

---

## 20. Exportações

Quando um módulo gerar artefatos, como PDF ou Excel, a geração deve ser isolada.

Fluxo recomendado:

```text
Route
 ↓
UseCase
 ↓
Exporter Port
 ↓
Exporter concreto
```

Exporters não devem ficar dentro da rota nem do repository.

---

## 21. Checklist para criar novo módulo de domínio

- [ ] Nome do contexto definido.
- [ ] Base path definido.
- [ ] Entidades principais definidas.
- [ ] Value objects definidos quando necessário.
- [ ] Use cases definidos.
- [ ] Ports definidos.
- [ ] Repositories concretos definidos.
- [ ] Composer criado.
- [ ] Rotas HTTP criadas.
- [ ] Datasource definido.
- [ ] Migrations definidas.
- [ ] Permissões definidas.
- [ ] Manifesto do plugin atualizado.
- [ ] Auditoria considerada.
- [ ] Testes de use case previstos.
- [ ] Não há regra de negócio na rota.

---

## 22. Pontos de atenção

1. Módulo de domínio não é controller grande.
2. Domínio não deve conhecer HTTP.
3. Use case não deve conhecer SQL.
4. Repository não deve decidir regra central.
5. Composer deve montar dependências.
6. TOTVS é integração, não dono dos módulos novos.
7. `postgres-plugins` é o banco correto para domínios novos de plugins.
8. Permissões devem ser granulares.
9. Módulo de qualidade exige auditoria.
10. Rotas reais devem ser confirmadas no código antes de documentação definitiva de endpoints implementados.

---

## 23. Documentos relacionados

```text
docs/07-api-delpi/visao-geral-api-delpi.md
docs/07-api-delpi/integracao-totvs.md
docs/07-api-delpi/banco-postgres-plugins.md
docs/07-api-delpi/rotas-operacionais.md
docs/08-plugins/qualidade.md
docs/11-padroes-de-desenvolvimento/padrao-de-use-case.md
```
