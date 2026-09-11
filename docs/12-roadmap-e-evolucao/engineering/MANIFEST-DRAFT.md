# Portal de Engenharia — manifesto lógico

> **Status:** draft funcional; não registrar no Core sem revalidar schema de manifesto vigente.  
> **Id alvo:** `engineering`  
> **basePath alvo:** `/apps/engineering`

## 1. Princípio

O Portal Engenharia deve aparecer como **um único app/módulo** no launcher global da Minha DELPI. As páginas internas são rotas do próprio MFE, não apps independentes.

O manifesto real deve seguir o schema vigente do Core no momento do E1. Não copiar `schemaVersion` histórico sem inspeção do contrato atual.

## 2. Identidade

```text
id: engineering
name: Portal de Engenharia
type: microfrontend
basePath: /apps/engineering
entry: /apps/engineering/assets/remoteEntry.js
renderMode: federated
```

Ícone sugerido deve vir do catálogo suportado pelo Portal, preferencialmente equivalente a `drafting-compass` se continuar válido.

## 3. Permission catalog lógico

P0 proposto:

```text
engineering.access
engineering.analytics.access
engineering.lmps.access
engineering.products.access
engineering.documents.access
engineering.nonconformities.write
engineering.costs.view
```

`engineering.administration.manage` só entra quando existir uma superfície administrativa P0/P1 aprovada.

O manifesto não deve inflar permissions para Sala/Tasks enquanto `engineering.access` + resource/self scope forem suficientes.

## 4. Rotas estáticas candidatas

| Path | Label | Permission | Menu global |
|---|---|---|---|
| `/apps/engineering` | Portal de Engenharia | `engineering.access` | sim |
| `/apps/engineering/overview` | Visão geral | `engineering.analytics.access` | não |
| `/apps/engineering/rooms` | Sala de interação | `engineering.access` | não |
| `/apps/engineering/my-tasks` | Minhas tarefas | `engineering.access` | não |
| `/apps/engineering/lmps` | LMPs | `engineering.lmps.access` | não |
| `/apps/engineering/help` | Ajuda | `engineering.access` | não |
| `/apps/engineering/tools/products` | Produtos | `engineering.products.access` | não |
| `/apps/engineering/tools/drawings` | Biblioteca de desenhos | policy definida no E0 | não |
| `/apps/engineering/tools/documents` | Documentos técnicos | `engineering.documents.access` | não |
| `/apps/engineering/tools/raw-material-control` | Controle de MP | `engineering.access` + owner downstream | não |
| `/apps/engineering/tools/transforma-plus` | TRANSFORMA+ | `engineering.access` + owner downstream | não |

Rotas dinâmicas como `/rooms/:roomId`, `/lmps/:saleNumber` e `/tools/products/:code` devem ser resolvidas pelo SPA e só entram no manifesto se o schema atual suportar parâmetros; não inventar path incompatível.

## 5. Navegação interna

O Core controla quais rotas/apps o usuário pode abrir; a TopBar interna mantém a ordem:

```text
Início → Visão geral → Sala de interação → Minhas tarefas → LMPs → Ajuda
```

O MFE pode omitir item sem capability, mas o backend continua sendo a barreira de segurança.

## 6. Versionamento

- SemVer;
- bump de versão quando o manifesto/rotas/permissions mudar materialmente;
- não fazer downgrade silencioso;
- registrar manifesto de forma idempotente conforme scripts atuais;
- preservar coexistência com manifests de `dashboard-engineering` e `dashboard-lmps` até cutover.

## 7. Manifesto × legados

No primeiro release do Portal:

```text
engineering                → ativo
dashboard-engineering      → continua ativo
dashboard-lmps             → continua ativo
```

Depois de paridade e soft cutover, os legados podem sair do launcher/menu ou redirecionar, mas só em etapa separada e reversível.

## 8. Gate de registro

Antes de registrar:

- schema do manifesto atual confirmado no Core;
- id `engineering` sem colisão;
- basePath/entry sem colisão;
- permission codes validados;
- rotas estáticas compatíveis;
- remoteEntry 200;
- MFE federado monta/desmonta sem erro;
- API/gateway healthy quando shell depender dela;
- persona autorizada e persona negativa preparadas.

## 9. Testes contratuais

Criar testes que garantam:

- id/basePath/entry coerentes;
- rotas começam com basePath;
- permission referenciada por rota existe no catálogo;
- só root aparece no launcher global, salvo decisão posterior;
- rotas internas não colidem;
- manifest version válido;
- sem permission duplicada;
- `engineering.access` protege a entrada do app.
