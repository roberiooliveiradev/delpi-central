# Minha DELPI — API DELPI: Rotas Operacionais

> **Arquivo:** `docs/07-api-delpi/rotas-operacionais.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** padrão de documentação das rotas operacionais da `api-delpi` e rotas conhecidas a partir dos arquivos enviados

---

## 1. Objetivo

Este documento organiza as rotas operacionais da **API DELPI**.

A API DELPI é o backend operacional da Minha DELPI. Ela pode expor rotas para consultas TOTVS, módulos de domínio, plugins e integrações.

> Observação importante: este documento não inventa endpoints não confirmados. As rotas listadas aqui são as rotas documentadas nos arquivos enviados, especialmente a especificação do módulo de não conformidades externas. O inventário completo de rotas da `api-delpi` deve ser complementado após análise direta dos arquivos reais de router/controller da `api-delpi`.

---

## 2. Base pública esperada

A API DELPI é exposta pelo Gateway.

Base conceitual:

```text
/apps/api-delpi
```

Módulos internos podem usar subpaths a partir dessa base.

Exemplo:

```text
/apps/api-delpi/quality/external-nc
```

---

## 3. Regras gerais para rotas operacionais

Rotas operacionais devem seguir estes princípios:

- validar JWT quando protegidas;
- validar permissões quando manipulam recurso sensível;
- manter regra de negócio em use cases;
- não conter SQL direto na rota;
- chamar composer/use case;
- retornar respostas padronizadas;
- documentar query params, body e erros;
- paginar listagens;
- manter separação entre TOTVS e `postgres-plugins`.

---

## 4. Fluxo arquitetural recomendado

Fluxo oficial recomendado para uma rota:

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

Esse fluxo evita que a rota conheça detalhes de banco ou concentre regra de negócio.

---

## 5. Modelo de documentação por rota

Cada rota deve ser documentada neste formato:

```markdown
## METHOD /path

### Objetivo

### Autenticação

### Permissões

### Query params

### Path params

### Body

### Resposta de sucesso

### Erros

### Datasource

### Use case

### Observações
```

Campos mínimos:

| Campo | Obrigatório |
|---|---:|
| Método HTTP | Sim |
| Path | Sim |
| Objetivo | Sim |
| Autenticação | Sim |
| Permissões | Quando houver |
| Datasource | Sim |
| Use case | Quando implementado |
| Exemplo de resposta | Recomendado |

---

## 6. Rotas confirmadas por especificação — Qualidade / External NC

A especificação técnica do plugin de não conformidades externas define o backend como um novo contexto dentro da `api-delpi`, com base:

```text
/apps/api-delpi/quality/external-nc
```

Essas rotas estão documentadas como plano/contrato técnico do módulo. Confirmar implementação final nos arquivos de código quando o módulo estiver presente no repositório.

---

## 7. Ocorrências

### 7.1 `GET /apps/api-delpi/quality/external-nc/nonconformities`

Objetivo:

```text
Listar ocorrências de não conformidade externa.
```

Uso esperado:

- listagem paginada;
- filtros por status;
- filtros por fornecedor;
- filtros por severidade;
- filtros por período;
- apoio à tela principal do plugin.

Datasource:

```text
postgres-plugins / schema quality
```

Use case esperado:

```text
ListExternalNonconformitiesUseCase
```

---

### 7.2 `POST /apps/api-delpi/quality/external-nc/nonconformities`

Objetivo:

```text
Criar nova ocorrência de não conformidade externa.
```

Use case esperado:

```text
CreateExternalNonconformityUseCase
```

Regras esperadas:

- gerar código sequencial;
- registrar usuário de abertura;
- validar campos obrigatórios;
- persistir dados principais;
- permitir anexos/evidências em fluxo complementar.

---

### 7.3 `GET /apps/api-delpi/quality/external-nc/nonconformities/{id}`

Objetivo:

```text
Obter detalhes de uma ocorrência.
```

Use case esperado:

```text
GetExternalNonconformityDetailsUseCase
```

A resposta deve reunir dados da ocorrência, causa raiz, ações, anexos, comentários, equipe e histórico, conforme implementação.

---

### 7.4 `PATCH /apps/api-delpi/quality/external-nc/nonconformities/{id}`

Objetivo:

```text
Atualizar dados de uma ocorrência.
```

Use case esperado:

```text
UpdateExternalNonconformityUseCase
```

A atualização deve respeitar o workflow e impedir alterações incompatíveis com o status.

---

### 7.5 `POST /apps/api-delpi/quality/external-nc/nonconformities/{id}/transition`

Objetivo:

```text
Executar transição de status da ocorrência.
```

Use case esperado:

```text
TransitionExternalNonconformityStatusUseCase
```

Regras esperadas:

- impedir transições inválidas;
- exigir justificativa quando aplicável;
- registrar auditoria;
- impedir encerramento sem eficácia aprovada.

---

## 8. Causa raiz

### 8.1 `GET /apps/api-delpi/quality/external-nc/nonconformities/{id}/root-causes`

Objetivo:

```text
Listar análises de causa raiz da ocorrência.
```

Datasource:

```text
quality.external_nc_root_causes
```

---

### 8.2 `POST /apps/api-delpi/quality/external-nc/nonconformities/{id}/root-causes`

Objetivo:

```text
Adicionar causa raiz à ocorrência.
```

Use case esperado:

```text
AddRootCauseUseCase
```

Regras esperadas:

- suportar métodos como 5 porquês e Ishikawa;
- permitir marcar causa raiz principal;
- registrar usuário responsável pela análise.

---

## 9. Ações

### 9.1 `POST /apps/api-delpi/quality/external-nc/nonconformities/{id}/actions`

Objetivo:

```text
Criar ação vinculada a uma ocorrência.
```

Use case esperado:

```text
CreateActionUseCase
```

Regras esperadas:

- ação precisa ter responsável;
- ação precisa ter prazo;
- ação pode estar vinculada a causa raiz;
- ação deve ter tipo e status.

---

### 9.2 `PATCH /apps/api-delpi/quality/external-nc/actions/{id}`

Objetivo:

```text
Atualizar ação.
```

Use case esperado:

```text
UpdateActionUseCase
```

---

### 9.3 `POST /apps/api-delpi/quality/external-nc/actions/{id}/complete`

Objetivo:

```text
Concluir ação.
```

Use case esperado:

```text
CompleteActionUseCase
```

Regras esperadas:

- registrar data de conclusão;
- registrar notas de conclusão;
- bloquear conclusão inválida;
- gerar auditoria.

---

## 10. Eficácia

### 10.1 `POST /apps/api-delpi/quality/external-nc/nonconformities/{id}/effectiveness-checks`

Objetivo:

```text
Registrar verificação de eficácia.
```

Use case esperado:

```text
RegisterEffectivenessCheckUseCase
```

Regras esperadas:

- definir critério de validação;
- registrar resultado;
- permitir reabertura quando eficácia não for aprovada;
- bloquear encerramento sem eficácia aprovada.

---

## 11. Comentários

### 11.1 `GET /apps/api-delpi/quality/external-nc/nonconformities/{id}/comments`

Objetivo:

```text
Listar comentários da ocorrência.
```

---

### 11.2 `POST /apps/api-delpi/quality/external-nc/nonconformities/{id}/comments`

Objetivo:

```text
Adicionar comentário à ocorrência.
```

Use case esperado:

```text
AddCommentUseCase
```

Regras esperadas:

- registrar autor;
- registrar data;
- distinguir comentário interno quando aplicável;
- preservar histórico.

---

## 12. Anexos

### 12.1 `POST /apps/api-delpi/quality/external-nc/nonconformities/{id}/attachments`

Objetivo:

```text
Enviar anexo vinculado à ocorrência.
```

Use case esperado:

```text
UploadAttachmentUseCase
```

---

### 12.2 `POST /apps/api-delpi/quality/external-nc/actions/{id}/attachments`

Objetivo:

```text
Enviar anexo vinculado a uma ação.
```

Regras esperadas:

- armazenar metadados do arquivo;
- desacoplar storage físico da tabela;
- registrar usuário de upload;
- permitir anexos em múltiplos níveis.

---

## 13. Dashboard

### 13.1 `GET /apps/api-delpi/quality/external-nc/dashboard/summary`

Objetivo:

```text
Obter resumo gerencial do módulo.
```

---

### 13.2 `GET /apps/api-delpi/quality/external-nc/dashboard/by-supplier`

Objetivo:

```text
Obter indicadores por fornecedor.
```

---

### 13.3 `GET /apps/api-delpi/quality/external-nc/dashboard/by-cause`

Objetivo:

```text
Obter indicadores por causa.
```

---

### 13.4 `GET /apps/api-delpi/quality/external-nc/dashboard/overdue-actions`

Objetivo:

```text
Listar ações vencidas ou indicadores de vencimento.
```

Use case esperado para dashboard:

```text
GetExternalNcDashboardUseCase
```

---

## 14. Exportação

### 14.1 `GET /apps/api-delpi/quality/external-nc/nonconformities/{id}/export`

Objetivo:

```text
Exportar relatório da ocorrência.
```

Use case esperado:

```text
ExportNonconformityReportUseCase
```

Formatos futuros possíveis:

- PDF;
- Excel;
- relatório final do caso.

---

## 15. Rotas TOTVS

Os arquivos enviados confirmam que a API DELPI possui conexão operacional com TOTVS por variáveis `DB_*` mapeadas a partir de `TOTVS_*`.

No entanto, a lista exata de endpoints TOTVS implementados depende dos arquivos reais de rota/controller da `api-delpi`.

Para não inventar endpoints, este documento não lista rotas TOTVS específicas sem confirmação de código.

Quando os routers reais forem analisados, criar seções por domínio:

```text
Produtos
Fornecedores
Clientes
Estoque
Compras
Vendas
Estruturas
Movimentos
Exportações
```

---

## 16. Autenticação

Rotas protegidas devem aceitar:

```http
Authorization: Bearer <access_token>
```

A API DELPI deve validar:

- assinatura;
- issuer;
- audience;
- expiração;
- algoritmo permitido;
- claims necessárias.

---

## 17. Permissões

Rotas operacionais sensíveis devem validar permissões.

Exemplo para qualidade:

```text
quality.external-nc.view
quality.external-nc.create
quality.external-nc.edit
quality.external-nc.close
quality.external-nc.dashboard.view
quality.external-nc.admin
```

A permissão deve ser registrada no manifesto do plugin e atribuída via RBAC na Core API.

---

## 18. Checklist para documentar nova rota

- [ ] Método HTTP confirmado no código.
- [ ] Path confirmado no código.
- [ ] Router/controller identificado.
- [ ] Use case identificado.
- [ ] Datasource identificado.
- [ ] Autenticação documentada.
- [ ] Permissões documentadas.
- [ ] Query params documentados.
- [ ] Body documentado.
- [ ] Respostas documentadas.
- [ ] Erros documentados.
- [ ] Consumidores conhecidos documentados.

---

## 19. Pendência controlada

Este documento deve ser complementado quando forem disponibilizados/analisados os arquivos reais da `api-delpi`, especialmente:

```text
app/interfaces/http/routes/
app/interface/http/routes/
app/main.py
app/application/use_cases/
app/composition/
app/infrastructure/persistence/
```

Sem esses arquivos, qualquer inventário completo de rotas operacionais seria especulativo.

---

## 20. Documentos relacionados

```text
docs/07-api-delpi/visao-geral-api-delpi.md
docs/07-api-delpi/integracao-totvs.md
docs/07-api-delpi/banco-postgres-plugins.md
docs/07-api-delpi/modulos-de-dominio.md
docs/08-plugins/qualidade.md
```
