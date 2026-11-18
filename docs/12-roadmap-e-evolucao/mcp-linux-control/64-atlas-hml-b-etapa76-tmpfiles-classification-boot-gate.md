# ATLAS | Etapa 76: classificação tmpfiles + correções do gate 75

**18/11/2026 | Issue #232 | source-only | status=blocked | PREPARE/ACT OFF**

## Correções

1. Auditor stage74/76 classifica regras com `critical` / `review` / `info` / `residual`.
2. Alertas Ubuntu 24.04 observados no srv-api (journal dinâmico, `d /var/lib`, basename
   `screen-cleanup.conf`) passam a `info` quando não há sobreposição exclusiva ATLAS.
3. Operações recursivas em ancestrais (`Z`/`R`/`A`/`T`/`H`) permanecem `critical`.
4. Gate stage75: serialização JSON via `dataclasses.asdict` (sem `__dict__` em slots),
   GID 0 apenas para grupo `root`, CLI estruturada, pós-criação fail-closed.

## Exceção Verifier (owner)

O owner dispensou o DELPI Verifier **somente** para este pacote da Etapa 76.
A dispensa **não** é aprovação de segurança, instalação ou produção. Proposta formal
em `AGENTS.md` (seção ATLAS Etapa 76) aguarda merge/aprovação do owner.

## Não feito

Sem install, deploy, pull no srv-api, PREPARE/ACT ou alteração de configs do SO.
