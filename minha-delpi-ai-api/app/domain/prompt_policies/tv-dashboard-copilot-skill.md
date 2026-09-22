# Skill `tv-dashboard-copilot` — RETIRADA

Esta skill está **desligada**. Mutações de programação/slides do TV Dashboard
passam pelo especialista **VISTA** (Custom GPT Actions em `/gpt-actions/v1`),
usando o motor canônico **PresentationMutation** + `TvPresentationWriteService`.

Não use a tool `tv_dashboard_copilot` nem `/data/copilot/*` (HTTP 410 Gone).

Se o usuário pedir alterações no TV Dashboard pelo Chat interno, oriente-o a
usar o especialista VISTA / fluxo gpt-actions — não reimplemente patch tipado
aqui.
