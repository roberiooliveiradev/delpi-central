# Fase 1 — status dos contratos M DELPI

> **Status:** implementação concluída em 2026-07-16; gate global de build com pendências preexistentes
> **Baseline:** `aa42803268de6341327ecb9cc483a71388507a12`
> **Flags:** `mQuery.enabled=false`, `mQuery.writeV2Enabled=false`

## Entregue

- domínio puro `tv_app/domain/data_query`: `SourceRange`, `Diagnostic`, tipos M, schema de coluna e `TransformPlan` tipado/imutável;
- adapter das 15 operações `dataTransform.steps` para `TransformPlan`;
- formatter legado para script M canônico, sem parser M;
- paridade entre execução v1 direta e plano adaptado nas fixtures compartilhadas;
- contrato explícito v1/v2, sanitização e dual-read;
- v2 seguro: script é preservado, mas não compilado nem executado; o reader retorna `m.execution_feature_disabled`;
- single-write v2 condicionado exclusivamente a `mQuery.writeV2Enabled`; a flag permanece desligada;
- sanitização impede persistência de `resolved`, AST, plano compilado e linhas;
- fingerprint de cache por identidade/credencial opaca, permissões e contexto de serviço, sem token bruto;
- enforcement de filial por `tvConstraints.requiresBranchPermission` e aliases canônicos;
- fallback `branchPolicy.compatibilityFallbackForUncuratedRoutes=true` mantém o comportamento das rotas sem curadoria.

## Contrato persistido

Leitura:

```text
v1 { steps } OU v2 { version: 2, language: "m-delpi-v1", script }
```

Escrita:

```text
writeV2Enabled=false → v1 continua v1
writeV2Enabled=true  → v1 é formatado e persistido somente como v2
```

Nunca são persistidos `ast`, `plan`, `rows`, preview ou diagnósticos como fonte de verdade.

## Allowlist e filial

As 232 rotas GET foram mantidas. A Fase 1 não realizou poda massiva:

- `requiresBranchPermission=true`: enforcement por aliases declarados na rota ou aliases canônicos globais;
- `requiresBranchPermission=false`: rota explicitamente não exige o escopo filial do TV;
- metadata ausente: fallback compatível permanece ativo até inventário e rollout curado.

O próximo rollout deve medir quantas rotas continuam sem marker antes de desligar o fallback.

## Fora de escopo

- lexer/parser e AST M;
- análise semântica;
- execução de script M;
- endpoints `/data/m/*`;
- execução M no browser;
- ativação de escrita v2.

Esses itens permanecem para a Fase 2 ou posterior.

## Validação

- backend Fase 0/1, transformador, sanitização e enrichment: **79 testes verdes**;
- apresentação compartilhada: **327 testes verdes**;
- frontend Preparar dados: **7 testes verdes**;
- allowlist: **232 rotas GET alinhadas ao OpenAPI**;
- build global do `tv-dashboard`: bloqueado no typecheck por erros já presentes em módulos fora do escopo (67 diagnósticos em `plugin-ui`, telas nativas, links de view e editores);
- gate gerador do catálogo: inventário preserva 232 rotas, mas há drift documental preexistente em 123 entradas; não foi aplicado `--write` em massa sem rollout/curadoria.
