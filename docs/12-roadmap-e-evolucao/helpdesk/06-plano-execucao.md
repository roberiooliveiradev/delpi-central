# 06 — Plano de execução

> **Status:** `PLANNED / NOT_STARTED`
> **Esta é a ordem.** [`05-roadmap.md`](./05-roadmap.md) só mostra as ondas.
> **Requisitos:** [`07-requisitos.md`](./07-requisitos.md)
> **Prova:** [`09-testes-e-aceite.md`](./09-testes-e-aceite.md)

Nenhuma subetapa abaixo foi executada. Documentação desta pasta não conta como `E1`.

## Antes × depois

| Caso | Antes | Depois | Muda? |
|---|---|---|---|
| Colaborador abre chamado | Sai para o GLPI ou cai no iframe | Abre na Minha DELPI, chamado no GLPI em nome dela | sim |
| Técnico opera a fila | Console GLPI | Console GLPI | não |
| API legada | desligada | desligada | não |
| Pessoa sem `helpdesk.access` | não entra no módulo | 403 no BFF e no portal | não |
| Pessoa com acesso no portal e sem direito no GLPI | — | 403 `glpi_forbidden`, sem chamado criado | sim, passa a ser explícito |
| Segundo clique no mesmo envio | — | um chamado só | sim |

## E1 — BFF e sessão OAuth

Depende de H0, já `PROVEN`.

### E1.S1 — Scaffold da helpdesk-api

API do bounded context, camadas domain / application / adapters, health, configuração por ambiente, sem chamada ao GLPI ainda.

Aceite: sobe com health ok; domínio não importa framework nem cliente HTTP.

Cobre: HD-001, HD-002.

### E1.S2 — Start, callback e sessão cifrada

`/auth/glpi/start`, `/auth/glpi/callback`, `/auth/glpi/session`, `DELETE` da sessão. PKCE, `state` de uso único, troca do código no servidor, refresh cifrado ligado ao `sub`.

Aceite: usuário A não lê sessão de B; callback com `state` inválido não grava token; segredo não aparece em log.

Cobre: HD-003, HD-004, HD-005.

### E1.S3 — Gateway, Compose e segredo

Rota `/apps/helpdesk-api`, serviço no Compose, variáveis documentadas sem valor. Client id e segredo só no ambiente.

Aceite: MFE futuro e curl autenticado chegam na API pelo gateway; repositório sem segredo.

Cobre: HD-006.

## E2 — Leitura

Depende de E1.

### E2.S1 — Categorias e urgências

Cliente HLAPI com timeout. Paths de dropdown confirmados em `/api.php/doc.json` do GLPI 11.0.5 e fixados no adapter, não no MFE.

Aceite: a lista muda se o GLPI mudar; não há lista hardcoded de categoria.

Cobre: HD-007.

### E2.S2 — Meus chamados e detalhe

`GET /tickets` e `GET /tickets/{id}` com timeline.

Aceite: a lista é a que o token GLPI devolve; chamado de outra pessoa invisível para esse perfil volta 404 ou 403, nunca o corpo; lista vazia é 200.

Cobre: HD-008, HD-009.

## E3 — Escrita

Depende de E2, porque categoria e urgência vêm da leitura.

### E3.S1 — Abrir chamado

`POST /tickets` com `Idempotency-Key`. Sem solicitante e sem entidade no payload. Sem retry.

Aceite: um chamado no GLPI com o usuário do token como solicitante; repetir a mesma chave não cria outro; chave ausente é 400.

Cobre: HD-010, HD-011, HD-012.

### E3.S2 — Acompanhamento

`POST /tickets/{id}/followups`.

Aceite: o texto aparece na timeline desse chamado; chamado invisível não recebe o texto; mesma chave não duplica.

Cobre: HD-013.

## E4 — Tela

Depende de E2 e E3 publicados no gateway.

### E4.S1 — MFE no lugar do iframe

`plugins/helpdesk` passa a microfrontend federado em `/apps/helpdesk`. O manifest iframe só é trocado nesta etapa, depois do fluxo da API existir.

Aceite: a rota do portal abre a tela nativa com o título Meus Chamados de TI; build do plugin passa.

Cobre: HD-014.

### E4.S2 — Lista, abertura e detalhe

Estados carregando, vazio, erro, acesso negado, link OAuth pendente. Detalhe em URL estável. Desktop e largura estreita.

Aceite: dá para abrir um chamado e ver o detalhe recarregando a página; 403 do GLPI não vira lista vazia.

Cobre: HD-015.

### E4.S3 — Ajuda in-app

Manual e textos de campo em português de negócio, sem path técnico.

Aceite: a ajuda descreve abrir, listar e acompanhar.

Cobre: HD-016.

### E4.S4 — Corte do iframe

Manifest `type: microfrontend`, permissão `helpdesk.access` mantida. Quem ainda abrir o path antigo do iframe cai em `/apps/helpdesk`.

Aceite: o menu mostra uma entrada, **Meus Chamados de TI**, e não restam duas telas.

Cobre: HD-017.

## E5 — Prova de ponta a ponta

Depende de E4.

### E5.S1 — Positive, irmão e negativo

Automatizado no BFF, mais o fluxo de tela coberto em [`09-testes-e-aceite.md`](./09-testes-e-aceite.md).

Cobre: HD-018.

### E5.S2 — Homologação com usuário real

Um colaborador com perfil de chamado abre um chamado de teste na Minha DELPI e o mesmo número aparece no GLPI em nome dele. Um usuário sem direito no GLPI recebe acesso negado. O console do técnico não muda.

Aceite registrado no ledger. Sem isso, H4 não está `PROVEN` em produção.

## Fora deste plano

H5 de [`05-roadmap.md`](./05-roadmap.md). Não criar etapa especulativa para anexo ou fila técnica.

## Revisão adversarial

- O escopo `api` é largo. A mitigação travada é perfil GLPI + superfície mínima do BFF, não um escopo que o GLPI 11.0.5 não tem.
- O iframe atual aponta para um host errado. Corrigir o iframe no meio de E1 criaria duas experiências. O corte fica em E4.S4.
- Dropdown de categoria ainda não teve o path gravado campo a campo. E2.S1 é a etapa que fecha isso no OpenAPI vivo, antes da tela.
- Chamado duplicado é o risco da escrita. Idempotência e ausência de retry estão em E3, não como ajuste posterior.
