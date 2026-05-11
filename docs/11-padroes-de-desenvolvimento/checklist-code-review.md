# Minha DELPI — Checklist de Code Review

> **Arquivo:** `docs/11-padroes-de-desenvolvimento/checklist-code-review.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** checklist para revisão de código em Core API, API DELPI, Portal e plugins

---

## 1. Objetivo

Este documento define um checklist de code review para mudanças na Minha DELPI.

Ele deve ser usado para revisar PRs e evitar regressões arquiteturais, problemas de segurança e inconsistências de documentação.

---

## 2. Checklist geral

- [ ] A mudança tem objetivo claro.
- [ ] O código está no módulo correto.
- [ ] Não mistura responsabilidades.
- [ ] Não duplica regra existente.
- [ ] Não adiciona dependência desnecessária.
- [ ] Não expõe segredo.
- [ ] Não quebra contratos existentes.
- [ ] Documentação foi atualizada quando necessário.
- [ ] Testes foram adicionados ou ajustados.

---

## 3. Rotas HTTP

- [ ] Rota tem método HTTP correto.
- [ ] Nome da rota é orientado a recurso.
- [ ] Rota valida entrada básica.
- [ ] Rota chama use case.
- [ ] Rota não contém SQL.
- [ ] Rota não contém regra de negócio extensa.
- [ ] Rota usa autenticação quando necessário.
- [ ] Rota usa permissão quando necessário.
- [ ] Erros seguem `{ errors: [...] }`.
- [ ] Status HTTP está correto.

---

## 4. Use cases

- [ ] Nome é orientado a ação.
- [ ] Possui método `execute`.
- [ ] Recebe dependências no construtor.
- [ ] Não acessa Flask diretamente.
- [ ] Não retorna `jsonify`.
- [ ] Não contém SQL direto.
- [ ] Usa repository/port.
- [ ] Valida regra de aplicação.
- [ ] Coleta eventos quando necessário.
- [ ] Não publica Socket.IO diretamente.
- [ ] Não faz commit indevido.
- [ ] Possui testes.

---

## 5. Repositories

- [ ] Repository tem responsabilidade clara.
- [ ] Não contém HTTP.
- [ ] Não publica eventos.
- [ ] Não decide autorização final.
- [ ] Não faz commit surpresa.
- [ ] Usa conexão/sessão correta.
- [ ] SQL é parametrizado.
- [ ] Paginação existe quando necessário.
- [ ] TOTVS e `postgres-plugins` não foram misturados.
- [ ] Métodos têm nomes claros.

---

## 6. Unit of Work e transações

- [ ] Transação tem fronteira clara.
- [ ] Commit ocorre no lugar correto.
- [ ] Rollback é tratado.
- [ ] Eventos são publicados após commit.
- [ ] Repositories compartilham sessão quando necessário.
- [ ] Não há commit duplo sem justificativa.
- [ ] Não há nested UoW desnecessário.

---

## 7. Eventos e Socket.IO

- [ ] Evento representa fato ocorrido.
- [ ] `entity` está correto.
- [ ] `action` está correto.
- [ ] Payload é mínimo.
- [ ] Payload não contém segredo.
- [ ] Evento é coletado no use case.
- [ ] Handler interno foi atualizado, se necessário.
- [ ] Portal sabe reagir, se aplicável.
- [ ] Cache RBAC é invalidado quando necessário.

---

## 8. RBAC e segurança

- [ ] Backend valida permissão.
- [ ] Frontend não é a única barreira.
- [ ] Superadmin foi tratado corretamente.
- [ ] Não é possível remover último superadmin.
- [ ] Alterações RBAC invalidam cache.
- [ ] Token não é colocado em query string.
- [ ] JWT valida issuer e audience.
- [ ] Dados sensíveis não vão para logs.
- [ ] Secrets não foram commitados.

---

## 9. Plugin System

- [ ] Manifesto segue schema.
- [ ] `schemaVersion` está correto.
- [ ] `id` é estável.
- [ ] `version` segue SemVer.
- [ ] `permissions.module` é igual ao plugin.
- [ ] Rotas usam permissões declaradas.
- [ ] `basePath` está coerente.
- [ ] `entry` está coerente com Gateway.
- [ ] Tipo do plugin está correto.
- [ ] Alteração estrutural usa nova versão.

---

## 10. Portal Frontend

- [ ] Não há plugin hardcoded sem necessidade.
- [ ] Menu vem de `/me/apps`.
- [ ] Token não é persistido indevidamente.
- [ ] Erros são tratados pelo `code`.
- [ ] Estado de loading/erro existe.
- [ ] Permissão no frontend é apenas UX.
- [ ] Backend continua protegendo ações.
- [ ] Microfrontend usa contrato `mount`/`unmount` quando federado.

---

## 11. API DELPI

- [ ] Rota segue Clean Architecture.
- [ ] Route chama composer/use case.
- [ ] Use case depende de port.
- [ ] Repository concreto está em infraestrutura.
- [ ] TOTVS e `postgres-plugins` estão separados.
- [ ] Endpoint protegido valida JWT.
- [ ] Permissões operacionais são verificadas.
- [ ] Respostas e erros estão documentados.

---

## 12. Banco e migrations

- [ ] Alteração de model possui migration.
- [ ] Migration foi revisada.
- [ ] Não há drop acidental.
- [ ] Índices foram considerados.
- [ ] FKs/constraints estão corretas.
- [ ] Seeds não substituem migrations.
- [ ] Dados existentes foram considerados.
- [ ] Reset local não foi usado como solução de produção.

---

## 13. Documentação

- [ ] Documento afetado foi atualizado.
- [ ] Novo endpoint foi documentado.
- [ ] Novo manifesto foi documentado.
- [ ] Nova variável de ambiente foi documentada.
- [ ] Nova tabela foi documentada.
- [ ] Nova permissão foi documentada.
- [ ] Roadmap/pendências foram atualizados, se aplicável.

---

## 14. Checklist final antes de aprovar

- [ ] Código compila/sobe localmente.
- [ ] Testes relevantes passaram.
- [ ] Logs não expõem dados sensíveis.
- [ ] Nenhuma credencial foi adicionada.
- [ ] Arquitetura foi respeitada.
- [ ] Contratos públicos foram preservados.
- [ ] Documentação está consistente.
- [ ] PR está pequeno o suficiente para revisão segura.

---

## 15. Documentos relacionados

```text
docs/11-padroes-de-desenvolvimento/padrao-de-rota.md
docs/11-padroes-de-desenvolvimento/padrao-de-use-case.md
docs/11-padroes-de-desenvolvimento/padrao-de-repository.md
docs/11-padroes-de-desenvolvimento/padrao-de-erro.md
docs/11-padroes-de-desenvolvimento/padrao-de-evento.md
```
