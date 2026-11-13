# Delpi Remote | G2-S1: coletor local Windows

**Data:** 2026-11-13
**Estado:** EM REVISAO. Codigo de coleta manual, sem instalacao, tarefas agendadas, S2S, API de envio, migration ou deploy produtivo.

## Entrega

- [Script de coleta local](../../../../it-portal-api/collectors/windows_workstation/Collect-ItPortalWorkstationSnapshot.ps1): PowerShell 5.1, somente consultas CIM/WMI do host atual.
- [Validador de contrato](../../../../it-portal-api/it_portal_app/domain/workstation_snapshots.py): Python puro, schema estrito e sanitizado.
- [Testes](../../../../it-portal-api/tests/test_workstation_snapshots.py): cenarios de dados validos, limites e rejeicoes.
- Contrato v1: source=windows_workstation_local_v1, schema_version=1, run_id UUIDv4, observed_at UTC, status, host.hostname, hardware (modelo, fabricante, CPU, memoria), os (versao/build/uptime), volumes (discos fixos), network.private_ipv4, sections_status.
- Sem coleta de usuarios, documentos, clipboard, processos, senha, credenciais, serial BIOS ou MAC. IP publico nunca e consultado; apenas IPv4 RFC1918 com opt-in.
- Snapshot **nao** altera o cadastro curado do Portal (nome, responsavel, setor etc.). Hostname e run_id nao comprovam identidade.

## Piloto manual em computador corporativo aprovado

1. Copiar o arquivo PowerShell por meio de checkout confiavel ou baixar pelo link do GitHub e revisar o codigo. Evitar executar codigo remoto em pipeline. Nao e necessario executar como Administrador para consultas CIM habituais.
2. Hash SHA-256 do script nesta revisao (mudara se o arquivo mudar ou sofrer conversao de finais de linha):

   d01ac5be57807e0421e38d0282e617e2e4059a2d7bafc5be9dc75a1ab9bf1e1c

3. Em PowerShell, na pasta do arquivo, executar:

    $snapshot = & ".\Collect-ItPortalWorkstationSnapshot.ps1" | ConvertFrom-Json
    $snapshot | Select-Object source, schema_version, status, observed_at
    $snapshot.hardware
    $snapshot.os
    $snapshot.volumes

4. Somente se houver necessidade de IPs privados, repetir com o parametro -IncludePrivateIPv4:

    $snapshot = & ".\Collect-ItPortalWorkstationSnapshot.ps1" -IncludePrivateIPv4 | ConvertFrom-Json
    $snapshot.network

5. Nao publicar JSON de computador real, hostname ou IP em repo/issue publico. Registrar resultado sem identificadores no diario de execucao. Nao usar bypass de politica de execucao como atalho; tratar assinatura/permissao pela politica de TI.
6. Nao instalar servico ou ScheduledTask: nesta etapa o script apenas produz um JSON no stdout, sem envio automatico.

## Validacoes e limites

- Executados em ambiente isolado: **9 testes unitarios de Python aprovados**, compilacao de sintaxe Python aprovada.
- Verificacao estatica do PowerShell: sem HTTP, instalacao, controle de host ou usuario. **Nao houve execucao real em Windows 10/11 nem parse por PowerShell 5.1** neste ambiente; permanece obrigatoria a validacao Windows.
- Validador exige tamanho total de ate 32768 bytes, maximo 16 volumes e 16 IPs, horario ate 24h atras e tolerancia de 5min futuros. Rejeita IP publico, segredos por chaves inesperadas, campos nao previstos, disk free > capacity, UUID invalido e status inconsistente.
- Nao foram introduzidas rotas, permissoes, variaveis de ambiente, migrations, arquivos de credencial ou componentes de acesso remoto.

## G2-S2: identidade e ingestao segura em revisao

Planejar e testar antes de implementar: identidade tecnica **individual e revogavel** por workstation (nunca baseada em IP, hostname ou serial); escopo S2S exclusivo it-portal.workstations.ingest, distinto dos agentes de servidor e motor remoto; short-lived tokens Keycloak com client_id associado de forma privada ao UUID do computador aprovado; binding vazio = proibido; revogacao e rotacao de segredo, endpoint S2S com rate-limit/limite de tamanho, validação, UTC, protecao replay por (workstation_id, run_id), retencao e auditoria; migration aditiva propria para dados observados, leitura apenas sob computers.view, sem sobrescrever campos curados e sem conceder acesso grafico.

Somente depois do desenho de seguranca e testes da autenticacao em homologacao habilitar o primeiro piloto com trafego. G0-SEC permanece gate para o futuro motor de acesso remoto.

## Rollback

O G2-S1 nao modificou banco nem producao. Basta nao executar/remover a copia do script na maquina piloto. Sem tarefa, agente instalado, canal remoto ou credencial para revogar.

Referencias: [Roadmap](README.md), [Arquitetura](ARCHITECTURE.md), [Seguranca](SECURITY-GATES.md), [Diario](EXECUTION-LOG.md), [Issue #179](https://github.com/roberiooliveiradev/delpi-central/issues/179).

**Atualizacao de 13/11/2026:** G2-S2 implementado em codigo, feature flag off e testes ainda nao executados com dependencias reais. Ver [G2-S2](G2-S2-S2S-INGEST-RELEASE.md). O script G2-S1 continua dependendo de piloto Windows 5.1 antes da ingestao habilitada.
