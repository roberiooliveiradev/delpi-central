# ADR-001 — Bounded context do Portal de Engenharia

- **Status:** Accepted para planejamento
- **Data:** 2026-09-11
- **Decisão:** criar `plugins/engineering` + `engineering-api` como boundary do Portal.

## Contexto

A experiência de Engenharia está distribuída entre `dashboard-engineering`, `dashboard-lmps`, Controle MP, Transformômetro e contratos `api-delpi`. Centralizar a experiência sem boundary próprio levaria o MFE a chamar múltiplos serviços, duplicar autorização e acoplar UI a payloads de providers.

## Decisão

```text
Browser → Portal → plugins/engineering → engineering-api → owners externos
```

`engineering-api` é BFF/contexto do Portal e owner somente de estado próprio, como Sala de interação e composições. Ele acessa outros domínios por ports/adapters HTTP.

## Consequências

Positivas:

- UI desacoplada de providers;
- AuthZ centralizado no backend;
- DTOs de anti-corruption;
- degradação parcial controlada;
- observabilidade por downstream;
- espaço próprio para Sala/documentos.

Custos:

- novo serviço/container;
- contratos BFF adicionais;
- necessidade de paridade/cutover progressivo.

## Proibições

- MFE chamar `api-delpi` diretamente;
- MFE chamar `commercial-api` para Sala;
- `engineering-api` importar domain/use case de outro serviço;
- copiar TOTVS/SI/requests/Transformômetro como nova fonte de verdade.

## Validação

E0 deve confirmar padrões atuais de Flask, auth resolver, manifesto, Compose/Gateway e banco/migrations antes do scaffold.
