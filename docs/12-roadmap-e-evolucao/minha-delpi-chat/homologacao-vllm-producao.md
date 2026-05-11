# Homologação vLLM em Produção — Minha DELPI Chat

## Objetivo

Validar o uso de vLLM como provider produtivo do Minha DELPI Chat, mantendo o backend `minha-delpi-ai-api` desacoplado por `LlmGatewayPort` e configurado por variável de ambiente.

## Premissas arquiteturais

- Desenvolvimento local usa Ollama.
- Produção usa vLLM.
- A solução continua 100% open source/self-hosted.
- Nenhum dado interno é enviado para APIs proprietárias de LLM.
- O LLM não acessa banco diretamente.
- Toda consulta operacional continua passando por tools, use cases, ports, RBAC e auditoria.

## Identificação do ambiente

Preencher antes do teste:

    Data:
    Responsável:
    Servidor:
    Sistema operacional:
    Docker version:
    NVIDIA driver:
    CUDA:
    GPU:
    VRAM:
    Branch:
    Commit:
    Tag:

## Modelo candidato

Preencher:

    Modelo:
    Licença:
    Tamanho:
    Context length:
    Motivo da escolha:

Candidatos iniciais:

    Qwen2.5 7B/14B/32B Instruct
    Llama 3.1/3.2 Instruct
    Mistral Instruct
    Gemma Instruct

## Variáveis de ambiente esperadas

    LLM_PROVIDER=vllm
    VLLM_BASE_URL=http://vllm:8000/v1
    VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct
    VLLM_API_KEY=<definir_secret_real>
    VLLM_TIMEOUT_SECONDS=300
    LLM_TEMPERATURE=0.2
    LLM_MAX_TOKENS=1024

## Checklist de infraestrutura

- [ ] Host possui GPU compatível.
- [ ] Driver NVIDIA instalado.
- [ ] Docker enxerga GPU.
- [ ] `nvidia-smi` funciona no host.
- [ ] Container vLLM enxerga GPU.
- [ ] Volume de cache HuggingFace configurado.
- [ ] `VLLM_API_KEY` definido fora do Git.
- [ ] Porta interna `8000` acessível para `minha-delpi-ai-api`.
- [ ] Gateway externo não expõe vLLM diretamente.

## Teste 1 — GPU no host

    nvidia-smi

Resultado esperado:

    GPU listada com VRAM disponível.

## Teste 2 — GPU via Docker

    docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi

Resultado esperado:

    Container lista a GPU.

## Teste 3 — Subir vLLM isolado

    docker run --rm --gpus all \
      --ipc=host \
      -p 8000:8000 \
      -e VLLM_API_KEY="$VLLM_API_KEY" \
      -v ~/.cache/huggingface:/root/.cache/huggingface \
      vllm/vllm-openai:latest \
      --model "$VLLM_MODEL" \
      --host 0.0.0.0 \
      --port 8000 \
      --api-key "$VLLM_API_KEY" \
      --max-model-len 8192

## Teste 4 — Listar modelos vLLM

    curl -s \
      -H "Authorization: Bearer $VLLM_API_KEY" \
      http://localhost:8000/v1/models | python3 -m json.tool

Resultado esperado:

    Modelo configurado aparece na resposta.

## Teste 5 — Chat completion direto no vLLM

    curl -s \
      -H "Authorization: Bearer $VLLM_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "model": "'"$VLLM_MODEL"'",
        "messages": [
          {
            "role": "user",
            "content": "Responda em uma frase: o que é a Minha DELPI?"
          }
        ],
        "temperature": 0.2,
        "max_tokens": 128
      }' \
      http://localhost:8000/v1/chat/completions | python3 -m json.tool

Resultado esperado:

    Resposta textual válida, sem erro 401/404/500.

## Teste 6 — Backend usando vLLM

No ambiente produtivo ou staging:

    curl -s \
      -H "Authorization: Bearer $TOKEN" \
      http://localhost/apps/minha-delpi-ai/api/admin/llm/status | python3 -m json.tool

Resultado esperado:

    {
      "provider": "vllm",
      "model": "...",
      "temperature": 0.2,
      "maxTokens": 1024
    }

## Teste 7 — Chat via Minha DELPI Chat

    SESSION_ID="$(
      curl -s \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"title":"Homologação vLLM","context":"geral"}' \
        http://localhost/apps/minha-delpi-ai/api/chat/sessions \
        | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])'
    )"

    curl -N \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"message":"O que é a Minha DELPI? Responda objetivamente.","context":"geral"}' \
      http://localhost/apps/minha-delpi-ai/api/chat/sessions/$SESSION_ID/messages/stream

Resultado esperado:

- [ ] `event: sources` aparece.
- [ ] `event: token` aparece.
- [ ] `event: done` aparece.
- [ ] Resposta não usa API proprietária.
- [ ] Mensagem é persistida no histórico.
- [ ] Auditoria é registrada.

## Medições mínimas

Preencher:

    Modelo:
    GPU:
    VRAM usada em repouso:
    VRAM usada em geração:
    Tempo para primeiro token:
    Tempo total resposta curta:
    Tempo total resposta com RAG:
    Erros encontrados:
    Observações:

## Critérios de aceite

- [ ] `LLM_PROVIDER=vllm`.
- [ ] `GET /admin/llm/status` retorna `provider=vllm`.
- [ ] Chat responde via backend sem mudar use case.
- [ ] Streaming funciona.
- [ ] Auditoria funciona.
- [ ] RAG continua funcionando.
- [ ] Tools continuam funcionando.
- [ ] Nenhuma API proprietária é usada.
- [ ] vLLM não fica exposto publicamente.
- [ ] Latência está dentro do aceitável para uso interno.
- [ ] Consumo de VRAM é compatível com o host.

## Plano de rollback

Se vLLM falhar em produção:

1. Alterar `LLM_PROVIDER=ollama` apenas em ambiente de contingência, se Ollama estiver disponível no host.
2. Ou retirar o plugin dos perfis finais temporariamente.
3. Manter dados e migrations intactos.
4. Registrar incidente e logs.
5. Revalidar modelo menor ou parâmetros de memória.

## Pendências pós-homologação

- Definir modelo produtivo oficial.
- Definir concorrência máxima.
- Definir autoscaling ou réplica única.
- Definir métricas Prometheus.
- Definir alerta de erro/latência.
- Definir política de atualização de modelo.

## Execução em srv-api

### Resultado da verificação de GPU

Data: 2026-05-11  
Servidor: srv-api  
Resultado: bloqueado por ausência de GPU NVIDIA detectada no host.

Comandos executados:

    lspci | grep -i nvidia

Resultado:

    Sem retorno.

Comando executado:

    ls -l /dev/nvidia*

Resultado:

    ls: cannot access '/dev/nvidia*': No such file or directory

### Conclusão

O servidor `srv-api` não possui GPU NVIDIA disponível para homologação produtiva do vLLM com aceleração GPU.

A homologação produtiva com vLLM permanece pendente até provisionamento de um host com GPU NVIDIA compatível, driver instalado, `nvidia-smi` funcional e NVIDIA Container Toolkit configurado.

### Decisão temporária

Não subir vLLM como produção neste host.

Opções possíveis:

- Provisionar outro servidor com GPU para vLLM.
- Manter o `srv-api` usando provider alternativo apenas em contingência.
- Usar vLLM CPU somente para teste técnico, não como aceite produtivo.

## Decisão temporária — Ollama em produção

Data: 2026-05-11  
Servidor: srv-api  
Decisão: usar Ollama temporariamente em produção enquanto não houver host com GPU NVIDIA disponível para vLLM.

### Justificativa

A homologação vLLM com GPU foi bloqueada porque o servidor `srv-api` não possui GPU NVIDIA detectada:

    lspci | grep -i nvidia
    # sem retorno

    ls -l /dev/nvidia*
    # No such file or directory

Como a solução deve permanecer 100% open source/self-hosted e não pode usar serviços proprietários de LLM, será usado Ollama como provider produtivo provisório.

### Condições da exceção

- Não usar OpenAI, Azure OpenAI, Anthropic, Gemini ou serviços fechados.
- Manter `LlmGatewayPort` e troca por variável de ambiente.
- Manter RAG, RBAC, auditoria e tools autorizadas.
- Registrar que vLLM continua pendente para produção definitiva.
- Revisar essa decisão quando houver servidor com GPU.

### Configuração provisória

    LLM_PROVIDER=ollama
    OLLAMA_BASE_URL=http://ollama:11434
    OLLAMA_MODEL=qwen2.5:1.5b
    OLLAMA_TIMEOUT_SECONDS=300
    LLM_TEMPERATURE=0.2
    LLM_MAX_TOKENS=1024

### Critério de aceite provisório

- `GET /admin/llm/status` retorna `provider=ollama`.
- Chat responde via streaming.
- RAG continua funcionando.
- Tools continuam funcionando.
- Auditoria continua funcionando.
- Nenhuma API proprietária é usada.

### Pendência

Homologar vLLM em servidor com GPU NVIDIA compatível.

## Decisão temporária — Ollama em produção

Data: 2026-05-11  
Servidor avaliado: srv-api  
Decisão: usar Ollama temporariamente em produção enquanto não houver host com GPU NVIDIA disponível para vLLM.

### Justificativa

A homologação vLLM com GPU foi bloqueada porque o servidor `srv-api` não possui GPU NVIDIA detectada:

    lspci | grep -i nvidia
    # sem retorno

    ls -l /dev/nvidia*
    # No such file or directory

Como a solução deve permanecer 100% open source/self-hosted e não pode usar serviços proprietários de LLM, será usado Ollama como provider produtivo provisório.

### Condições da exceção

- Não usar OpenAI, Azure OpenAI, Anthropic, Gemini ou serviços fechados.
- Manter `LlmGatewayPort` e troca por variável de ambiente.
- Manter RAG, RBAC, auditoria e tools autorizadas.
- Registrar que vLLM continua pendente para produção definitiva.
- Revisar essa decisão quando houver servidor com GPU.

### Configuração provisória

    LLM_PROVIDER=ollama
    OLLAMA_BASE_URL=http://ollama:11434
    OLLAMA_MODEL=qwen2.5:1.5b
    OLLAMA_TIMEOUT_SECONDS=300
    LLM_TEMPERATURE=0.2
    LLM_MAX_TOKENS=1024

### Critério de aceite provisório

- `GET /admin/llm/status` retorna `provider=ollama`.
- Chat responde via streaming.
- RAG continua funcionando.
- Tools continuam funcionando.
- Auditoria continua funcionando.
- Nenhuma API proprietária é usada.

### Pendência

Homologar vLLM em servidor com GPU NVIDIA compatível.
