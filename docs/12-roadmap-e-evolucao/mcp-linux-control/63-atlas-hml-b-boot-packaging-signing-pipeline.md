# ATLAS | Pacote boot + packaging + pipeline de assinatura

**18/11/2026 | Issue #232 | source-only | status=blocked | PREPARE/ACT OFF**

## Escopo

Consolida, sem instalação no host:

1. Gate de ativação de boot (etapa 75) sobre os validadores 73/74.
2. Packaging-review separado dos `.candidate` (entrypoints disposable-only).
3. Pipeline de assinatura com socket UNIX real em fixture descartável.
4. Registro GLPI de metadados de chave (sem segredos).
5. Matriz de prontidão HML/PROD (blocked).

## Limites

Não executa instalação, reboot, keygen operacional, GLPI HTTP, deploy ou merge.
MCP permanece com exatamente quatro tools READ. Candidatos systemd continuam
não instaláveis. Autorização operacional do owner permanece obrigatória.
