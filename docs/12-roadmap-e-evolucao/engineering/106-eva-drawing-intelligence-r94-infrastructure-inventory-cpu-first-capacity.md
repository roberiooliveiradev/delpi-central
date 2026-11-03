# 106 — EVA Drawing Intelligence R9.4: Infrastructure Inventory & CPU-First Capacity Assessment

**Status:** inventário READ-ONLY completo em dev e prod (medições diretas, não herdadas); nenhum install/config/deploy; doc only. **Data:** 2026-11-02. Refs: 100–105.

## 1. Ambientes (medidos diretamente)

| | **Dev (WSL2, delpi166-pc)** | **Prod (srv-api, VM VMware)** |
|---|---|---|
| OS/Kernel | WSL2 6.18.33 x86_64 | Ubuntu 6.8.0-137-generic x86_64 |
| CPU | Intel Core 7 240H — 8 vCPU, 2 thr/core | Xeon Gold 5418Y — **16 vCPU**, 1 thr/core, L3 45MB |
| ISA | AVX, AVX2 (sem AVX-512) | **AVX-512 completo** (+VNNI) — favorável a inferência CPU |
| RAM | 9.7GiB total / **3.7GiB avail** | 23GiB total / **5.4GiB avail** |
| Swap | 6.0GiB / 1.1GiB livre | 4.0GiB / **232Ki livre — saturado** |
| Disco | 809G livre (16%) | **24G livre (88% usado)** |
| GPU | nenhuma | nenhuma (VMware SVGA — display only; confirma premissa CPU-first) |
| Docker | 29.7.2 | 29.2.1 |

## 2. Prod — containers e consumo (snapshot `docker stats --no-stream`)

~25 containers; engineering-api **278MB RSS, sem limites cgroup** (mem=0, cpus=0 — mesma política api-delpi/core/gateway). Maiores: delpi-languagetool 748MB (limite 2.4GiB), ollama 498MB (limite 4.4GiB), postgres-plugins 441MB. Total ~18GB usado de 23GB + swap cheio → **host já saturado de memória**. Disk 88% usado → espaço p/ modelos é restrito (~24G).

## 3. Configuração EVA atual

OCR subprocess isolado dentro do engineering-api (RLIMIT_AS 12GB nominal, CPU quota ~7 cores, timeout 300s, semáforo concorrência); modelos PaddleOCR det/rec read-only com checksums; OpenCV primitives; `engine_capabilities()` = 3 adapters registrados (só baseline executável).

## 4. Orçamento seguro de inferência

Host já saturado (swap cheio). **Orçamento seguro episódico ≈ 2–3GiB**, com ressalva: picos OCR existentes (~3GB histórico) já convivem no limite. Worker persistente na mesma VM: **inviável**.

| Cenário | Veredito |
|---|---|
| **A — VM atual, dentro do processo** | Viável SÓ p/ modelos ≤~2GB + baseline já aprovada |
| **B — worker isolado mesma VM** | **INVIÁVEL** — não há RAM ociosa p/ container dedicado persistente |
| **C — VM separada** | Requerida p/ PPS-v3 (≥12GiB dedicada) ou Docling estável; custo/sizing → owner infra |

## 5. Matriz CPU-first (viabilidade no orçamento ~2–3GiB)

| Motor | CPU ok | RAM est. | Exec. hoje | Nota |
|---|---|---|---|---|
| **A baseline** | ✔ AVX2 | ~3GB pico | **SIM** | único comprovado |
| **B Docling** | ✔ torch CPU | ~2–4GB | modelo bloqueado | venv lockfile docling (não pin manual) — Viável após fix de compat |
| **C PPS-v3** | ✔ AVX-512 | ~8–12GB init | **NÃO nesta VM** | requer Cenário C |
| **C' Paddle TableStructureRecognition (modelo único)** | ✔ | ~0.5–1.5GB | **Provável viável** | módulo isolado do paddlex — menor experimento p/ tabela |
| **D RapidOCR/ONNX compactos** | ✔ | ~0.5–1GB | Provável viável | ONNX CPU + modelos pequenos; licença Apache |

## 6. Menor experimento executável (recomendação)

**`paddleocr.TableStructureRecognition` isolado** no `90264302` — único modelo paddlex (não o pipeline completo): RAM ~0.5–1.5GB, dentro do orçamento episódico, prova se o reconhecimento de células paddle supera a heurística. Alternativa: Docling em venv com lockfile oficial (~4GB, borderline Cenário A). PPS-v3 completo = Cenário C (owner infra).
