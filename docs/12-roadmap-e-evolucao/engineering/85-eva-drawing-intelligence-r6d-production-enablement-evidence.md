# 85 — EVA Drawing Intelligence — Governed Production Benchmark Enablement & Real Provider Evidence

**Status:** IMPLEMENTED + DEPLOYED (flag ativa; providers reais disponíveis). **Data:** 2026-10-31. **SHA:** `9e0cc89d55` (main).

## 1. Enablement (E01/E02)

- `ENG_DRAWING_BENCHMARK_ENABLED` — adicionada ao env block do `engineering-api` em `infra/docker-compose.yml` com default `true` (kill switch: `.env`/env `false` → `feature_disabled` imediato, sem rebuild; restauração = remover/valor `false` + restart do container).
- Autorização por usuário permanece **RBAC real**: `engineering.access` + permissão do desenho via identidade delegada + `require_any_permission` no gateway — a flag é controle operacional de feature, **não** substitui AuthZ. Permissão dedicada `engineering.drawing_benchmark` não existe no Core → `ARCHITECTURE_DECISION_REQUIRED` registrado (seria gate adicional opcional; a proteção atual é suficiente para o escopo experimental controlado).

## 2. Dependências (E03)

- `pdfplumber==0.11.9` (MIT) + `pypdfium2==4.30.1` (BSD-3) adicionados a `engineering-api/requirements.txt` — pin do combo **validado no benchmark R6-B** (pdfplumber 0.11.10 exigia pypdfium2>=5.9.0 → ResolutionImpossible no primeiro build; corrigido para o par comprovado).
- Verificado **no container produtivo**: `pdfplumber 0.11.9` e `pypdfium2` importam sem erro; `pypdf 5.9.0` baseline intacto.

## 3. Limites / observabilidade / kill switch (E05/E06/E09)

- Limites vigentes: 15MB/30páginas/60k chars por provider; render pdfium ≤5p/300dpi; profile `approved_local_extractors` fixo backend — consumidor não escolhe provider/path/URL; `fields` ≤50.
- Kill switch: env `ENG_DRAWING_BENCHMARK_ENABLED=false` + `docker compose restart engineering-api` (ou down/up) → `feature_disabled` restaurado; `product.drawing_analysis` inalterado.
- Logs: sem tokens/PDF-integral/texto — contrato `drawing_benchmark.v1` nunca os inclui.

## 4. Deploy / verificação

- Commit `f6e15d05f2` (flag+deps) + `9e0cc89d55` (pin fix) → prod merge → `--build engineering-api` → `delpi-engineering-api Up (healthy)` com nova imagem.
- Container: `FLAG: true`, `pdfplumber 0.11.9`, `pypdfium2` OK.
- Autenticado E2E `analyze(product.drawing_benchmark)`: `TEST_NOT_RUN` — executor sem sessão OAuth do consumidor; ação pronta, flag ativa, providers reais — um usuário autorizado pode agora executar e obter matriz real (retornaria `feature_disabled`→agora permitido para identidade autorizada).

## 5. Matriz E-01..30

PASS: 01–14 (inventário, flag, authz, providers, perfil, limites, logs, kill switch, segurança, regressão, seis tools, sem legado, deploy), 23–27, 29–30. FEATURE_GATED parcial: 15–22 — execução real aguarda primeira chamada autenticada (infraestrutura pronta/verificada; resultado real ainda não consumido por usuário autorizado). TEST_NOT_RUN: smoke MCP autenticado.

## 6. Residuais

1. Primeira execução real `analyze(product.drawing_benchmark)` por consumidor autorizado → produzir matriz real em `90264302.pdf` (hash/deps verificados — falta apenas a chamada).
2. Permissão dedicada experimental no Core — decisão de owner.
3. OCR — contracts prontos; instalação pendente de evidência de gaps do benchmark real.
4. Rate/concurrency limits para benchmark — atuais limites de extração servem como proteção inicial; tuning dedicado = próxima etapa se uso exigir.
5. Prod repo divergido — merge não destrutivo documentado.
