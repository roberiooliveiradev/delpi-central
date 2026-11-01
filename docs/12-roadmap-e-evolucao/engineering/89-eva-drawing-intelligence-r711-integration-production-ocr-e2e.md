# 89 — EVA Drawing Intelligence R7.1.1: Git Integration Recovery, Isolated OCR Production Deployment & Memory-Limit Correction

**Status:** INTEGRATED + DEPLOYED (código em prod com flag OCR off) — E2E autenticado TEST_NOT_RUN (sem sessão OAuth consumidora). **Data:** 2026-11-01. **SHAs:**  (R7.1 integrado por terceiro),  (fix memória, meu commit), prod merge .

## 1. Reconciliação Git (I02/I03/I16)

- Commits locais R7.1 (, ) não constam como SHAs no remoto, porém o commit  (mesmo título/escopo) já havia integrado **conteúdo idêntico** — diff arquivo-a-arquivo local×remoto = vazio em , , , doc 88. Nenhum trabalho perdido; nada a re-aplicar.
- Workspace isolado usado: clone limpo  (árvore compartilhada permanecia contaminada com trabalho concorrente não-commitado — stash/commit-alheio proibidos e não necessários).
- Push realizado do clone:  em . Deploy canônico: Updating d199686f92..0f4ff1b3f9 no repo prod (padrão local-merge estabelecido) →  →  → .

## 2. Correção de memória — gate I06 (alta prioridade)

Medição real (venv py3.12, modelos provisionados, PDF oficial 90264302):

| Métrica | Valor |
|---|---|
| VmPeak (virtual) | **8,65 GB** (9066484 KB) |
| VmHWM (pico RSS) | **2,86 GB** (2997116 KB) |
| OCR resultado | 92 tokens / 762 chars — igual à R7 |

 **mataria** a execução real (cap de espaço de endereçamento virtual, não RSS). Correção: default  3072→**12288MB** (bounds 512–16384) + compose prod. Prova: pipeline completo  via  com cap 12GB → , , , 19,6s.

## 3. Isolamento/segurança revalidados

Timeout→SIGKILL+reap (testado), semáforo=1, hash mismatch rejeitado, request sem secrets/JWT/URL/path, modelos por  (vazio em prod → ), extras fora da imagem prod (INSTALL_VISION_EXTRAS=false). Suite no clone: 9/9 isolation + 97 focused R7 — verde.

## 4. Runtime prod verificado

 healthy; módulo carrega ;  (off, fail-closed); ; 6 tools MCP;  intocada. Kill switch: flag vazia = off; rollback = flag + SHA anterior.

## 5. E2E autenticado — estado honesto

: executor sem JWT de usuário produtivo (realm prod exige credencial humana que não possuo; dev realm 'rober' existe mas acervo dev está vazio — seed documentado como próximo passo). PaddleOCR indisponível na imagem prod por decisão de isolamento (extras opt-in) — perfil visual em prod retornaria / honesto até: extras na imagem + modelos provisionados + flag + sessão autorizada (cadeia de gates documentada).

## 6. Residuais

1. E2E autenticado  — requer: sessão OAuth + image extras + modelos + flag (owner).
2. Corpus autenticado via  (contrato confirmado, 4.833 PDFs offline).
3. Worker dedicado se volume crescer (ARCHITECTURE_DECISION_REQUIRED).
4. Permissão  no Core — decisão owner.
