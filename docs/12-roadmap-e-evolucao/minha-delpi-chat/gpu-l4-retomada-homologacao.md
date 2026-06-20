# GPU NVIDIA L4 — retomada da homologação LLM

> **Status:** planejamento (jun/2026)  
> **Objetivo:** registrar decisões da cotação e o plano de execução para retomar a conversa técnica assim que a GPU estiver instalada no `srv-api`.

Documentos relacionados:

- [homologacao-vllm-producao.md](./homologacao-vllm-producao.md) — checklist operacional vLLM (testes, aceite)
- [status-atual.md](./status-atual.md) — snapshot do chat em produção
- [variaveis-de-ambiente.md](../../02-infraestrutura/variaveis-de-ambiente.md) — catálogo de env vars
- [docker-compose.md](../../02-infraestrutura/docker-compose.md) — serviço `vllm` (profile `gpu`)

---

## Contexto da conversa (jun/2026)

Foi avaliada a cotação de uma **NVIDIA L4 24GB passiva** (Dell **490-BJRQ** / fabricante **707X1**) para substituir a inferência **CPU-only** do Minha DELPI Chat, hoje limitada a modelos pequenos no Ollama.

**Perguntas já respondidas nesta linha de trabalho:**

1. Quais modelos cabem na L4 e são melhores que `qwen2.5:3b` / `qwen2.5:7b`?
2. Todos são open source? → **Sim**, exceto Llama (licença Meta — evitar como padrão).
3. Ollama vs “modelo mais inteligente” → **Ollama é runtime**, não modelo; inteligência vem do peso (14B, 32B…) e do pipeline (RAG + tools).

**Decisão preliminar:** homologar **Qwen2.5-14B-Instruct** (ou **Qwen3-14B**) no **vLLM** como modelo principal; manter **`bge-m3`** no Ollama/CPU para embeddings.

---

## Situação atual do `srv-api` (pré-GPU)

Preencher/atualizar na retomada:

| Item | Valor conhecido (jun/2026) | Confirmar na instalação |
|------|----------------------------|-------------------------|
| Servidor | `srv-api` | |
| CPU | Intel Xeon Gold 5418Y, **4 vCPUs** | |
| RAM | **~8–15 GB** (docs divergem) | `free -h` |
| GPU | **Nenhuma** | `nvidia-smi` |
| Modelo PowerEdge | **A confirmar** | etiqueta / iDRAC |
| Provider LLM | `ollama` (CPU) | |
| Modelo chat | `qwen2.5:3b` | |
| Embeddings | `bge-m3` (Ollama) | |
| Stack | Docker Compose (`infra/docker-compose.yml`) | |

Configuração prod documentada em `infra/.env.prod` — ver comentários na seção «IA — Minha DELPI Chat».

---

## Hardware cotado

| Especificação | Valor |
|---------------|--------|
| GPU | NVIDIA **L4** Tensor Core |
| Arquitetura | Ada Lovelace |
| VRAM | **24 GB** GDDR6 |
| Interface | PCIe |
| TDP | **72 W** |
| Refrigeração | **Passiva** (exige fluxo de ar do chassi) |
| Formato | Full height, wide |
| Peça Dell | 490-BJRQ |
| Referência | [NVIDIA L4 24GB — Dell Brasil](https://www.dell.com/pt-br/shop/nvidia-l4-pcie-72w-24gb-passivo-solteiro-wide-altura-integral-gpu-instala%C3%A7%C3%A3o-pelo-cliente/apd/490-bjrq/pe%C3%A7as-baterias-e-atualiza%C3%A7%C3%B5es) |

### Compatibilidade Dell (lista oficial do produto)

Confirmar que o **modelo exato** do servidor está na lista, por exemplo: PowerEdge R650, R660, R750, R760, T560, etc. (lista completa na página Dell acima).

### Riscos de instalação

- [ ] Slot PCIe full-height disponível (riser/bracket corretos)
- [ ] Fluxo de ar adequado para GPU **passiva**
- [ ] Fonte/chassi suportam +72 W
- [ ] Driver NVIDIA + **NVIDIA Container Toolkit** no host
- [ ] RAM do host: **recomendado 32 GB** se possível (Postgres + APIs + Ollama embeddings + vLLM)

---

## Ollama ≠ modelo

| Conceito | O que é | Papel no DELPI |
|----------|---------|----------------|
| **Modelo** | Pesos do LLM (Qwen 3B, 14B, 32B…) | Define qualidade de linguagem/raciocínio |
| **Ollama** | Servidor de inferência | Hoje: chat + embeddings em CPU |
| **vLLM** | Servidor de inferência (GPU) | Alvo produtivo para chat com L4 |
| **Pipeline** | RAG, tools, route selection | Inteligência operacional transversal |

Trocar só o runtime **não** aumenta inteligência; é preciso **modelo maior** (e/ou melhor uso de RAG + tools).

---

## Modelos candidatos (somente Apache 2.0 / MIT)

### Recomendado — produção

| Modelo | Licença | VRAM (est.) | Contexto | Velocidade L4 (est.) | Uso |
|--------|---------|-------------|----------|----------------------|-----|
| **Qwen/Qwen2.5-14B-Instruct** | Apache 2.0 | ~15 GB (Q4/Q8) | 8K–16K | ~20–25 tok/s | **Principal** |
| **Qwen/Qwen3-14B-Instruct** | Apache 2.0 | ~15 GB | 8K–16K | similar | Alternativa |

### Máximo em 1× L4 (apertado)

| Modelo | Licença | VRAM (est.) | Contexto | Nota |
|--------|---------|-------------|----------|------|
| **Qwen/Qwen2.5-32B-Instruct** (AWQ/Q4) | Apache 2.0 | ~19–22 GB | 4K confortável | Modo «Pensador»; pouca margem |
| **Qwen/Qwen3-32B** (Q4) | Apache 2.0 | ~19–22 GB | 4K–8K no limite | Idem |
| **DeepSeek-R1-Distill-Qwen-32B** (Q4) | Apache 2.0 | ~19–22 GB | curto | Foco em raciocínio |

### Não priorizar neste host

| Modelo | Motivo |
|--------|--------|
| **Llama 3.x** | Licença Meta (não Apache/MIT estrito) |
| **70B** (qualquer quant.) | VRAM insuficiente ou qualidade ruim |
| **32B FP16/BF16** | ~65 GB VRAM |
| **Dois LLM grandes na mesma GPU** | Sem margem (chat + VLM) |

### Embeddings (manter)

| Modelo | Licença | Onde rodar |
|--------|---------|------------|
| **bge-m3** | MIT | **Ollama em CPU** — não competir VRAM com chat |

---

## Arquitetura alvo pós-GPU

```text
Usuário → minha-delpi-ai-api
              ├─ chat LLM  → vLLM (GPU L4) — Qwen 14B
              ├─ embeddings → Ollama (CPU) — bge-m3
              └─ tools/RAG  → pipeline existente (sem mudança de princípio)
```

Premissas (inalteradas):

- 100% open source / self-hosted
- Sem APIs proprietárias de LLM
- `LlmGatewayPort` — troca por `LLM_PROVIDER=vllm`
- vLLM **não** exposto publicamente; só rede interna Docker

---

## Variáveis de ambiente sugeridas (14B)

Ajustar `infra/.env.prod` após homologação:

```env
# Chat — vLLM na GPU
LLM_PROVIDER=vllm
VLLM_BASE_URL=http://vllm:8000/v1
VLLM_MODEL=Qwen/Qwen2.5-14B-Instruct
VLLM_API_KEY=<secret_forte>
VLLM_TIMEOUT_SECONDS=300
VLLM_MAX_MODEL_LEN=8192

LLM_TEMPERATURE=0.4
LLM_MAX_TOKENS=1536

# Embeddings — Ollama CPU (não migrar para GPU na 1ª fase)
EMBEDDING_MODEL=bge-m3
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MAX_LOADED_MODELS=1

# Modos de resposta (opcional)
CHAT_RESPONSE_MODE_FAST_MODEL=qwen2.5:3b
CHAT_RESPONSE_MODE_THINKER_MODEL=
CHAT_RESPONSE_MODE_THINKER_NUM_CTX=8192
```

Para **32B Q4** (se homologado como pensador):

```env
VLLM_MODEL=Qwen/Qwen2.5-32B-Instruct-AWQ
VLLM_MAX_MODEL_LEN=4096
```

---

## Checklist — antes de ligar vLLM em prod

### 1. Host

```bash
lspci | grep -i nvidia
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

### 2. Compose (profile `gpu`)

O serviço `vllm` já existe em `infra/docker-compose.yml` (profile `gpu`). Na retomada, validar se falta `deploy.resources.reservations.devices` (NVIDIA) no compose — adicionar se o container não enxergar GPU.

Subir stack:

```bash
cd ~/projetos/delpi-central
docker compose -f infra/docker-compose.yml \
  --env-file infra/.env.prod \
  --profile gpu \
  up -d vllm ollama minha-delpi-ai-api
```

### 3. Smoke test vLLM

```bash
curl -s http://localhost:8000/v1/models \
  -H "Authorization: Bearer $VLLM_API_KEY"
```

(Se vLLM não estiver publicado no host, executar curl de dentro da rede Docker ou via `docker exec`.)

### 4. API DELPI

```bash
curl -s https://minhadelpi.com.br/apps/minha-delpi-ai/api/admin/llm/status
```

Esperado: `provider=vllm`, modelo configurado.

### 5. Aceite funcional

Seguir testes completos em [homologacao-vllm-producao.md](./homologacao-vllm-producao.md):

- streaming de chat
- RAG com embeddings
- external actions / tools
- auditoria
- latência aceitável (~20 tok/s interativo)

---

## Registro de homologação (preencher na retomada)

| Campo | Valor |
|-------|--------|
| Data instalação GPU | |
| Modelo PowerEdge | |
| Driver NVIDIA | |
| CUDA | |
| VRAM detectada | |
| RAM host após upgrade | |
| Modelo homologado | |
| `VLLM_MAX_MODEL_LEN` | |
| Tok/s medidos | |
| Responsável | |
| Branch / commit | |
| Aceite produtivo? | ☐ Sim ☐ Não — motivo: |

---

## Pendências para decidir na retomada

1. **Modelo PowerEdge** — compatibilidade mecânica e térmica com L4 passiva.
2. **Upgrade de RAM** — 32 GB recomendado antes ou junto com a GPU?
3. **14B vs 32B Q4** — qualidade vs contexto vs latência para o chat operacional DELPI.
4. **Modos Rápida / Pensador** — manter 3b no Ollama para «Rápida» ou usar 7b na GPU?
5. **Compose GPU** — adicionar reserva NVIDIA explícita no serviço `vllm` se necessário.
6. **Quantização** — AWQ/GPTQ vs FP16 para 14B (FP16 cabe com folga na L4).
7. **OCR/visão** (`CHAT_DOCUMENT_VISION_PADDLE_USE_GPU`) — ligar GPU no Paddle após chat estável?

---

## Prompt para retomar com o assistente (Cursor)

Copiar e colar quando a GPU estiver instalada:

```text
Retomar homologação GPU conforme docs/12-roadmap-e-evolucao/minha-delpi-chat/gpu-l4-retomada-homologacao.md

Servidor: srv-api
GPU instalada: [modelo / nvidia-smi output]
RAM: [free -h]
PowerEdge: [modelo]

Quero:
1. Validar driver + Docker GPU + vLLM (profile gpu)
2. Homologar Qwen2.5-14B-Instruct (ou Qwen3-14B) como LLM_PROVIDER=vllm
3. Manter bge-m3 no Ollama para embeddings
4. Atualizar infra/.env.prod e documentar resultados no doc de retomada

Saída esperada: checklist preenchido, env vars finais, comandos de deploy e tok/s medidos.
```

---

## Histórico

| Data | Evento |
|------|--------|
| jun/2026 | Cotação Dell L4 24GB (~R$ 60.605); análise de modelos; decisão preliminar 14B + vLLM; criação deste documento |
| | GPU instalada — _pendente_ |
| | Homologação vLLM aceita — _pendente_ |
