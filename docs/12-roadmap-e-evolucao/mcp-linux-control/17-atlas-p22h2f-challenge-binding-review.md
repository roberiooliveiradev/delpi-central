# ATLAS | P2.2h.2f: vinculo do challenge OCI e preparacao de PREPARE

**Data:** 2026-11-16
**Status:** PR para revisao; **PREPARE_DISABLED / ACT_DISABLED**.
**Alvo:** somente integridade do journal OCI ja existente, sem novo endpoint de escrita.

## Contexto validado

A etapa P2.2h.2e liberou a consulta autenticada do journal em producao com role dedicada de SELECT. Nao ha fluxo autenticado de PREPARE, comprovante de host elegivel completo ou executor ACT.

## Falha evitada

No journal, o banco calcula o SHA-256 do nonce de 32 bytes e consome um challenge one-shot. Antes deste incremento, o contrato exigia que a intencao e a prova do host concordassem no hash, mas nao comparava aquele hash ao nonce realmente consumido. Assim, duas evidencias coerentes entre si poderiam apontar a outro challenge.

Esta PR exige comparacao constante `hmac.compare_digest(intent.host_challenge_sha256, digest)` antes das leituras de idempotencia e de qualquer escrita. Divergencia retorna `OCI_CHALLENGE_BINDING_MISMATCH`; o challenge continua nao consumido.

## Testes e escopo

- Fixture positiva liga intent, host proof e candidate ao exato nonce emitido.
- Casos existentes preservam idempotencia, replay, rollback, serializacao e isolamento por ambiente.
- Novo teste negativo garante que prova de outro challenge, mesmo internamente coerente, nao consome o challenge e nao cria proposta/evento/binding.
- A workflow `.github/workflows/atlas-p22e-integration.yml` executa testes em PostgreSQL descartavel em eventos pull_request e em main para estes caminhos.
- Validacao independente `delpi-verifier` e execucao de integracao no CI **pendentes de evidencias**. Sem afirmacao de PASS antes de observar resultados.

## Limites e proxima etapa

Proibir ACT/rollback automatizado e qualquer mutacao de servicos PROD. Nao criar API de PREPARE so a partir de dataclasses fornecidas pelo cliente: as provas CI/OCI e host devem vir de verificadores independentes, com identidade e permissao do Core conferidas. Exigir papel de escrita com menor privilegio, distinto de `it_portal_atlas_journal_reader`. Resolver idempotencia HTTP no PREPARE, risco de rollback e atestacao real antes do endpoint. Preservar operacao manual e regras do repositório.

## Fluxo de contribuicao adotado neste chat

Para este trabalho, alteracoes sao realizadas em branch de funcionalidade, publicadas por Pull Request e revisadas antes de merge. Nenhum commit direto em `main` nem deploy automatico sem autorizacao. Esta orientacao explicita do solicitante prevalece sobre a rotina padrao de commit direto descrita em `AGENTS.md` para este chat.
