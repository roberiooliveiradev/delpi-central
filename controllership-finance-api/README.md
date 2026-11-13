# controllership-finance-api

BFF do Portal Controladoria & Finanças.

## Lançamento de Notas Fiscais — tempo real

`LNF_REALTIME_ENABLED` default `false`. A rota WebSocket
`/lancamento-notas-fiscais/realtime` só existe quando esta flag e
`LNF_HOSTED_ENABLED` estão ligadas, e o processo é um só.

O hub fica na memória do processo. `WEB_CONCURRENCY`, `UVICORN_WORKERS` ou
`--workers` acima de 1 desligam o realtime no startup e registram
`lnf_realtime_disabled_multiple_workers`. Réplicas definidas fora do
processo não são visíveis aqui: a flag tem de permanecer desligada até
existir broker. O Dockerfile sobe o uvicorn sem `--workers`.

O access log redige o parâmetro `token`. Contrato:
`docs/12-roadmap-e-evolucao/controllership-finance/167-lnf-tempo-real-websocket.md`.
