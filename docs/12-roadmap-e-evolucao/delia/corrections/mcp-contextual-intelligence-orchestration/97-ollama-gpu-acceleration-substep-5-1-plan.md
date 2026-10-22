# DÉLIA — Subetapa 5.1: aceleração GPU do Ollama local

**Decisão do Product Master (2026-10-22):** inserir uma subetapa **5.1** entre **5. Painel Contexto** e **6. Homologação e ativação**. Esta é uma task bounded de infraestrutura/performance local; não substitui nem altera o escopo da etapa 5 ou 6.

**TASK_ID proposto:** `DELIA-C3-OLLAMA-GPU-LOCAL-ACCELERATION-05A-01`
**STATUS:** `EXECUTED` — ver seção "Resultado da execução" abaixo; aceite final reservado à coordenação.
**Owner:** infraestrutura de desenvolvimento / runtime Ollama; DÉLIA consome o modelo somente via adapter OpenAI-compatible existente.

## Evidência já disponível

Relatório 93 observou: RTX 3050 Laptop 6 GB no host; WSL ~7 GiB RAM; Ollama 0.40.8, modelo qwen2.5:3b Q4_K_M em container `delpi-ollama`; `ollama ps` mostrou `100% CPU`, GPU não passada ao container; compose limita memória do serviço a ~4500 MiB. Relatórios 93/96 descrevem timeouts sob CPU, limitações de JSON e avaliações multiturno inconclusivas. Hardware e configuração presentes no momento da execução futura devem ser revalidados.

## Objetivo e guardrails

Habilitar e comprovar aceleração GPU do **serviço Ollama existente** para testes locais DÉLIA, sem novo serviço, novo provider ou mudança no planner, contratos/model invocation, orçamentos 2/60/30, CRI, MCP, política de autorização ou produção. Todos os testes locais com LLM real seguem exclusivamente Ollama: chamadas externas pagas proibidas. Não prometer que GPU resolve aderência a JSON, semântica ou testes inconclusivos; medir separadamente.

## Execução autorizada somente após reancoragem

1. Verificar HEAD/origin, status/worktrees, Project Instructions/.cursor, autoridades 16→50→17→49→51→52→21→20→25, arquitetura, specs, ledger e docs 93/96, além do relatório da etapa 5.
2. Inventariar driver NVIDIA, WSL2, CUDA, integração Docker/NVIDIA Container Toolkit ou runtime aplicável, `/dev/dxg`, `nvidia-smi` e recursos atuais. Distinguir host, WSL, Docker e Ollama; não supor compatibilidade ou fazer alterações globais destrutivas.
3. Provar `EXISTING_EQUIVALENT` e `REUSE_DECISION` por responsabilidade. Reutilizar `infra/docker-compose.dev.yml` serviço Ollama e `OpenAICompatibleModelInvocationAdapter`; aplicar o menor diff necessário somente ao perfil local de infraestrutura, com rollback.
4. Testar o modelo atual aquecido em CPU com amostras baselines de latência, tokens/s, memória, JSON estruturado e casos operacionais. Habilitar exposição de GPU ao serviço autorizado, preservando segurança do host, limites de VRAM/RAM, compartilhamento e outras aplicações.
5. Verificar com `nvidia-smi`, `ollama ps` e telemetria de runtime que **a inferência real** utiliza GPU, não apenas que o dispositivo está visível. Registrar offload parcial ou total. Não alegar `GPU_PASS` só por detectar a placa.
6. Reexecutar exatamente os mesmos cenários de CPU em GPU; comparar cold/warm latency, tokens/s, p50/p95 se amostra suficiente, consumo VRAM/RAM, budgets de estágio e taxa de JSON válido. Documentar causalidade com cautela. Testar regressão determinística e bloqueio de egress externo.
7. Somente se os recursos permitirem, avaliar um modelo local maior/alternativo com comparação explícita, sem substituir automaticamente o modelo aprovado nem relaxar contratos/deadlines.
8. Documentar testes, configuração, SHA, ambiente, riscos, rollback e resultado; commit/push na main, verificar remoto e reportar à coordenação. Não modificar produção.

## Aceite

`GPU_AVAILABLE_TO_CONTAINER=YES` e `OLLAMA_INFERENCE_ON_GPU=PROVEN` via evidência do runner e telemetria, com regressão e nenhum egress para LLM externo; ou `BLOCKED/INCONCLUSIVE` se driver, WSL, Docker, recursos ou suporte técnico não permitirem, com causa e próxima dependência. Medição comparativa é obrigatória; resultado mais rápido não é presumido. O ganho de GPU não substitui homologação integrada nem fecha incidentes pendentes do CRI, DAVI ou fragmento Ori.

**Sequência:** Etapa 4 ACCEPT_WITH_RESIDUAL → Etapa 5 Painel Contexto → **Etapa 5.1 GPU Ollama** → Etapa 6 Homologação/ativação. `I04_ACCEPTED` e fase permanecem sujeitos ao HEAD/ledger e à coordenação.

## Resultado da execução (2026-10-22)

### Inventário medido

- **Host:** NVIDIA GeForce RTX 3050 Laptop 6 GB, driver 610.60, CUDA UMD 13.3, WDDM. GPU ociosa antes da mudança (~447 MiB em uso por processos do Windows).
- **WSL2:** Ubuntu 24.04, `/dev/dxg` presente, `nvidia-smi` funcional no WSL, 7.6 GiB RAM totais (~3 GiB disponíveis), swap 2 GiB. Bibliotecas NVIDIA de user-space expostas em `/usr/lib/wsl/lib` (`libcuda.so.1`, `libnvidia-ml`, `nvidia-smi`, `libdxcore`).
- **Docker:** engine nativa 29.7.2 dentro do WSL (não Docker Desktop), contexto default unix socket, runtime runc apenas — sem nvidia-container-toolkit e sem spec CDI (`docker run --gpus all` falhava com `failed to discover GPU vendor from CDI`).
- **Achado-chave:** CDI/toolkit exigiriam root para gerar `/etc/cdi` — indisponível. Alternativa mínima comprovada empiricamente: passar `/dev/dxg` + montar `/usr/lib/wsl` read-only + `LD_LIBRARY_PATH=/usr/lib/wsl/lib` torna NVML/CUDA funcionais no container **sem** toolkit, sem `--privileged` e sem alterar `daemon.json`. Montar apenas `/usr/lib/wsl/lib` não basta — o diretório completo é necessário.

### Configuração implementada

Arquivo novo `infra/docker-compose.ollama-gpu.yml` — overlay opt-in sobre o serviço `ollama` existente do `infra/docker-compose.dev.yml`:

```yaml
services:
  ollama:
    devices:
      - /dev/dxg
    volumes:
      - /usr/lib/wsl:/usr/lib/wsl:ro
    environment:
      LD_LIBRARY_PATH: /usr/lib/wsl/lib
```

Ativação: `docker compose -p infra -f infra/docker-compose.dev.yml -f infra/docker-compose.ollama-gpu.yml --profile optional-heavy up -d ollama`. Volume `infra_ollama_data`, rede `infra_delpi-network`, limite de memória `4500M` e restart policy preservados; nenhum outro serviço alterado. Em hosts sem WSL2/NVIDIA o overlay falha rápido e de forma explícita (ausência de `/dev/dxg`), sem degradar o compose base. Rollback CPU-only: omitir o overlay do `-f` e recriar — zero diff no arquivo base.

### Verificação GPU (inferência real, não apenas visibilidade)

- Log de startup: `inference compute id=0 library=CUDA compute=8.6 name=CUDA0 NVIDIA GeForce RTX 3050 6GB total=6.0GiB available=5.0GiB`.
- `ollama ps`: `qwen2.5:3b ... 100% GPU` — offload integral (no baseline era `100% CPU`).
- `nvidia-smi` durante geração: VRAM ~2.64 GiB consumida pelo modelo residente; utilização 4–18% em pulsos.
- Após `docker restart delpi-ollama`: redescoberta de CUDA0 e recarga do modelo a 100% GPU — estabilidade de restart comprovada.

### CPU baseline × GPU (mesmos cenários, modelo, adapter e budgets)

| Métrica | CPU | GPU | Diferença |
|---|---|---|---|
| Cold load (ollama /api) | 41.0s | 20.5s | −50% |
| Warm tokens/s (mediana) | 16.6 (12.1–21.8) | 47.4 (46.3–48.6) | ~2.9× |
| Prompt eval tokens/s | ~750–940 | ~2200 | ~2.8× |
| CPU do container na geração | ~790% sustentado | ~450–510% em burst curto | menor e muito mais curto |
| RAM do container | 2.31–2.45 GiB | 2.09 GiB | ~igual |
| VRAM | 0 | 2.64 GiB | +2.64 GiB |
| JSON direto (3 sondas, `format:json`) | 3/3 válido | 3/3 válido | sem mudança |
| Turnos wire T1–G3 (suite multiturn) | 30.0 / 34.8 / 22.0 / 43.7 / 12.1(timeout) / 46.8 s | 5.3 / 17.6 / 8.3 / 8.8 / 10.1 / 2.3 s | −49% a −95% |
| "Qual o último processo cadastrado?" | PROCESSING_TIMEOUT 52s, 0 invokes | CLARIFICATION_REQUIRED 10.9s, 1 invoke real | completa no budget |
| "Qual o primeiro processo no Transformômetro?" | PROCESSING_TIMEOUT 52s, 0 invokes | CLARIFICATION_REQUIRED 10.3s, 1 invoke real | completa no budget |
| Erros de estágio (wire, todas as sondas) | 11 em 46 chamadas — classe `timeout` | 4 em 38 chamadas — classe `invalid_structured_output` | timeouts → 0; erros semânticos persistem |
| PROCESSING_TIMEOUT total | 3 de 8 turnos lógicos | 0 de 8 | eliminados nesta amostra |

**Honestidade:** a GPU eliminou a classe `timeout` e quase triplicou o throughput, mas `invalid_structured_output` continua ocorrendo (4 ocorrências) — velocidade não implica aderência JSON nem qualidade semântica; essas dimensões permanecem medidas separadamente e cobertas pelos fallbacks governados existentes. Amostra pequena (3 warm + 8 turnos por braço); variabilidade entre turnos é alta por natureza estocástica do modelo ≤3B.

### Modelo maior (avaliação condicional)

`qwen2.5:7b-instruct-q4_K_M` (4.7 GB) avaliado: load 88.2s, offload **parcial 18% CPU / 82% GPU** (VRAM ~4.58 GiB, 5.2 GB residentes totais), warm 19.9 tokens/s — **pior** que 3b em GPU (47.4) e abaixo do necessário para os budgets 2/60/30 neste pipeline multiestágio. Modelo removido do volume após a medição. `MODEL_RECOMMENDATION=manter qwen2.5:3b`; 7b é inviável em 6 GiB de VRAM neste host. Nenhuma troca de modelo aplicada à configuração.

### Regressão e gates

- Suite backend `delia-api` completa no worktree da task sob ambiente GPU-ativo: **1972 passed, 3 skipped (pré-existentes), 0 failed**.
- Regressão real exercida pelas sondas wire acima (conectividade Ollama, adapter OpenAI-compatible, orquestração, continuidade multiturno, timeouts, MCP autenticado) e restart do container.
- `LOCAL_LLM_PROVIDER=OLLAMA_ONLY`, `EXTERNAL_LLM_LOCAL_CALLS=0`, `EXTERNAL_PAID_FALLBACK=PROHIBITED`, budgets `MAX_GOVERNED_ATTEMPTS=2 / 60s / 30s` inalterados, `PRODUCTION_RECOVERY=OFF`, produção intocada.
- Resíduo ambiental conhecido: WSL desconecta intermitentemente sob saturação (reconecta sozinho; observado durante a execução, sem perda de evidência).

### Arquivos alterados

- `infra/docker-compose.ollama-gpu.yml` (novo overlay WSL2 GPU — único diff de infraestrutura)
- este documento (status + resultado), README da trilha, execution ledger.
