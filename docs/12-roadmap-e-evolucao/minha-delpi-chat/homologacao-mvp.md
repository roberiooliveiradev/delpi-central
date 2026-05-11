# Homologação MVP — Minha DELPI Chat

## Escopo

Validação final do MVP do plugin oficial Minha DELPI Chat.

## Checklist funcional

- [ ] Healthcheck do backend retorna `200 OK`.
- [ ] `remoteEntry.js` retorna JavaScript.
- [ ] Plugin aparece no menu para usuário autorizado.
- [ ] Usuário sem permissão não acessa o chat.
- [ ] Usuário com `minha-delpi.chat.access` acessa o chat.
- [ ] Usuário com `minha-delpi.chat.ask` envia mensagem.
- [ ] Sessão é criada com `user_id` autenticado.
- [ ] Histórico é persistido.
- [ ] Usuário não acessa sessão de outro usuário.
- [ ] Streaming retorna `token`, `done` e `close`.
- [ ] RAG retorna fontes quando há documento ativo.
- [ ] Sem contexto suficiente, o chat informa limitação.
- [ ] Tool autorizada retorna dados limitados.
- [ ] Tool inexistente retorna erro padronizado.
- [ ] Tool sem permissão retorna `403`.
- [ ] Auditoria registra envio de mensagem.
- [ ] Auditoria registra tool call.
- [ ] Auditoria registra ação administrativa.
- [ ] Admin lista documentos.
- [ ] Admin desativa documento.
- [ ] Admin visualiza auditoria.
- [ ] Status LLM mostra provider atual.
- [ ] Dev usa Ollama.
- [ ] Produção está preparada para vLLM.

## Checklist arquitetural

- [ ] Não há OpenAI, Azure OpenAI, Anthropic ou Gemini.
- [ ] LLM não acessa banco diretamente.
- [ ] Toda ferramenta passa por RBAC.
- [ ] Nenhuma permissão efetiva é validada no frontend.
- [ ] Nenhum endpoint foi criado sem use case.
- [ ] Nenhum repository foi criado sem port.
- [ ] Alterações de banco possuem migration.
- [ ] Erros seguem envelope `errors[]`.
- [ ] Logs não expõem tokens.
- [ ] Prompt completo não é logado.
- [ ] Secrets não estão versionados.
- [ ] Manifesto usa `schemaVersion: 1.0.0`.
- [ ] Manifesto usa `id: minha-delpi-chat`.
- [ ] Manifesto aponta para `/apps/minha-delpi-chat/assets/remoteEntry.js`.

## Evidências

Preencher durante homologação:

```text
Data:
Branch:
Commit:
Ambiente:
Usuário admin:
Usuário comum:
Resultado geral:
Pendências: