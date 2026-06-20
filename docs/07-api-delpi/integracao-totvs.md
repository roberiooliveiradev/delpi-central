# Minha DELPI — API DELPI: Integração TOTVS

> **Arquivo:** `docs/07-api-delpi/integracao-totvs.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** integração da `api-delpi` com TOTVS e separação entre dados operacionais e dados de plugins

---

## 1. Objetivo

Este documento descreve como a **API DELPI** se relaciona com o TOTVS dentro da arquitetura da Minha DELPI.

A `api-delpi` é o backend operacional da plataforma. Ela concentra integrações e consultas de negócio, incluindo acesso ao datasource TOTVS, e também pode hospedar módulos de domínio que não pertencem à Core API.

---

## 2. Papel da API DELPI na integração TOTVS

A API DELPI atua como camada de backend para dados operacionais.

No contexto TOTVS, ela deve ser responsável por:

- consultar dados corporativos;
- expor endpoints operacionais para plugins e módulos;
- encapsular SQL, regras de acesso e detalhes do datasource;
- proteger endpoints com JWT quando necessário;
- separar consultas TOTVS de domínios novos persistidos no `postgres-plugins`.

A API DELPI não deve assumir responsabilidades da Core API, como RBAC central, registro de plugins, rotas do Portal ou manifestos.

---

## 3. Configuração no Docker Compose

No Compose, o serviço é:

```text
api-delpi
```

Container:

```text
delpi-api-delpi
```

Build:

```yaml
build:
  context: ..
  dockerfile: api-delpi/Dockerfile
```

O Compose informa que o código da API espera variáveis genéricas `DB_*`, mas essas variáveis são preenchidas com valores `TOTVS_*`.

Mapeamento:

```yaml
DB_HOST: ${TOTVS_DB_HOST}
DB_PORT: ${TOTVS_DB_PORT}
DB_USER: ${TOTVS_DB_USER}
DB_PASSWORD: ${TOTVS_DB_PASSWORD}
DB_DATABASE: ${TOTVS_DB_DATABASE}
```

Portanto, dentro do container da `api-delpi`, o datasource identificado por `DB_*` representa o banco TOTVS.

---

## 4. Variáveis de ambiente da integração TOTVS

Variáveis externas esperadas:

```env
TOTVS_DB_HOST=
TOTVS_DB_PORT=
TOTVS_DB_USER=
TOTVS_DB_PASSWORD=
TOTVS_DB_DATABASE=
```

Variáveis vistas pelo código dentro do container:

```env
DB_HOST=
DB_PORT=
DB_USER=
DB_PASSWORD=
DB_DATABASE=
```

Regra:

> `DB_*` na `api-delpi` deve ser entendido como conexão operacional TOTVS, não como banco da Core API.

---

## 5. Separação entre Core API e API DELPI

A integração TOTVS pertence à `api-delpi`.

Não pertence à Core API:

- consultas TOTVS;
- regras operacionais de produto, estoque, fornecedor, cliente ou pedidos;
- SQL de Protheus/TOTVS;
- módulos de domínio operacional.

Pertence à Core API:

- autenticação recebida via JWT;
- usuário local;
- RBAC;
- apps;
- rotas;
- manifestos;
- permissões;
- favoritos;
- notificações;
- governança central.

---

## 6. Separação entre TOTVS e `postgres-plugins`

A `api-delpi` possui dois tipos de datasource relevantes:

```text
TOTVS            → dados operacionais legados/corporativos
postgres-plugins → dados de módulos novos e plugins
```

A regra arquitetural é:

> Domínios novos de plugin não devem ser persistidos no banco TOTVS nem reutilizar infraestrutura de SQL Server/TOTVS quando o domínio pertence ao ecossistema de plugins.

Isso é especialmente importante para módulos como qualidade, que devem persistir dados próprios no `postgres-plugins`.

---

## 7. Clean Architecture na API DELPI

A documentação técnica de refatoração da `api-delpi` define que o projeto deve seguir Clean Architecture.

Fluxo recomendado para uma rota:

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

Responsabilidades:

| Camada | Responsabilidade |
|---|---|
| Route | Receber HTTP, validar entrada e chamar use case |
| Composer | Montar dependências concretas |
| Use case | Coordenar regra de aplicação |
| Port | Definir contrato abstrato |
| Repository concreto | Acessar TOTVS ou outro datasource |
| Domain | Modelar regra e conceitos centrais |

---

## 8. Repositories TOTVS

Repositories concretos ligados ao TOTVS devem ficar na camada de infraestrutura.

Exemplo conceitual:

```text
app/infrastructure/persistence/totvs/
```

Responsabilidades:

- montar SQL;
- executar consultas;
- retornar dados mapeados;
- encapsular diferenças do banco;
- não conhecer HTTP;
- não decidir autorização;
- não conter regra de negócio central.

---

## 9. O que não fazer

Evitar:

```text
Colocar SQL TOTVS diretamente em rotas HTTP.
Fazer use case depender de repository concreto.
Misturar regra de negócio no repository.
Misturar persistência de plugins no datasource TOTVS.
Reutilizar BaseRepository TOTVS para domínios PostgreSQL de plugins.
Retornar JSONResponse dentro de use case.
Usar API DELPI como Core API paralela.
```

---

## 10. Autenticação e autorização

A `api-delpi` recebe variáveis de JWT/Keycloak:

```env
KEYCLOAK_REALM=
KEYCLOAK_AUDIENCE=
KEYCLOAK_JWKS_URL=
KEYCLOAK_ISSUER=
JWT_ALGORITHMS=
JWT_SECRET=
```

Endpoints protegidos devem validar JWT.

Fluxo recomendado:

```text
Portal ou plugin envia Authorization: Bearer <token>
  ↓
Gateway roteia para api-delpi
  ↓
api-delpi valida assinatura, issuer, audience e expiração
  ↓
api-delpi executa regra operacional
```

Quando uma rota operacional exigir permissão específica, a API DELPI deve validar o permission code esperado.

---

## 11. Relação com plugins

Plugins frontend podem consumir dados TOTVS por meio da API DELPI.

Fluxo:

```text
Portal carrega plugin autorizado
  ↓
Plugin chama endpoint da api-delpi
  ↓
api-delpi valida JWT
  ↓
api-delpi consulta TOTVS
  ↓
api-delpi retorna dados operacionais
```

A governança de acesso ao plugin no menu vem da Core API. A proteção dos dados retornados pela API DELPI deve existir no próprio backend operacional.

---

## 12. TOTVS como integração futura de módulos de plugin

No módulo de qualidade, a especificação técnica indica que integrações futuras com TOTVS podem envolver:

- fornecedor;
- pedido de compra;
- nota fiscal;
- material;
- lote;
- custo.

Essas integrações devem complementar o domínio do plugin sem transformar o banco TOTVS no local de persistência do novo domínio.

---

## 13. Checklist para novas rotas TOTVS

Antes de publicar uma rota operacional baseada em TOTVS:

- [ ] A rota está na camada HTTP.
- [ ] Existe use case.
- [ ] Existe port.
- [ ] Repository concreto acessa o TOTVS.
- [ ] A rota não contém SQL.
- [ ] O use case não conhece HTTP.
- [ ] O repository não decide regra de autorização.
- [ ] O endpoint valida JWT quando protegido.
- [ ] A resposta não expõe dados sensíveis desnecessários.
- [ ] Há paginação quando a consulta pode retornar muitos registros.

---

## 14. Pontos de atenção

1. `DB_*` dentro da API DELPI representa TOTVS.
2. A Core API não deve consultar TOTVS.
3. Domínios novos de plugins devem usar `postgres-plugins`.
4. Não misturar SQL Server/TOTVS com PostgreSQL de plugins.
5. JWT deve ser validado em endpoints protegidos.
6. O Portal não substitui validação de segurança no backend.
7. Repositories TOTVS não devem conter regra HTTP.
8. Use cases não devem depender de repository concreto.
9. Integrações TOTVS devem ser encapsuladas e documentadas por rota.
10. A documentação de rotas TOTVS depende da leitura dos arquivos reais da `api-delpi`.

---

## 15. Documentos relacionados

```text
docs/07-api-delpi/visao-geral-api-delpi.md
docs/07-api-delpi/banco-postgres-plugins.md
docs/07-api-delpi/rotas-operacionais.md
docs/07-api-delpi/modulos-de-dominio.md
docs/11-padroes-de-desenvolvimento/padrao-de-rota.md
docs/11-padroes-de-desenvolvimento/padrao-de-repository.md
```
