# DÉLIA — Subetapa 5.1: aceleração GPU do Ollama local

**Decisão do Product Master (2026-10-22):** inserir uma subetapa **5.1** entre **5. Painel Contexto** e **6. Homologação e ativação**. Esta é uma task bounded de infraestrutura/performance local; não substitui nem altera o escopo da etapa 5 ou 6.

**TASK_ID proposto:** `DELIA-C3-OLLAMA-GPU-LOCAL-ACCELERATION-05A-01`
**STATUS:** `PLANNED`; não executada; hardware/runtime requer inventário atual.
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
