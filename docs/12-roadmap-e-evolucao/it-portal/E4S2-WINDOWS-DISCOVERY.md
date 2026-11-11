# E4.S2 — descoberta local de servidores Windows (piloto controlado)

Status: **DIAGNOSTIC_ONLY / EXECUÇÃO MANUAL VALIDADA** em um Windows Server 2019 em 11/11/2026. Esta fatia não habilita coleta automatizada, monitoramento contínuo ou alertas. A integração API/UI está proposta separadamente em [E4.S3](E4S3-WINDOWS-OBSERVATIONS.md), sem deploy comprovado.

## Contexto comprovado

- Owner do cadastro: `it-portal-api`; frontend: `plugins/it-portal`.
- O piloto Linux `srv-api` concluiu smoke manual produtivo e tem timer horário habilitado, conforme solução GLPI #1571 em 11/11/2026. Duas execuções automáticas consecutivas ainda não estavam demonstradas na solução.
- Contrato atual `observations.py` aceita somente `source=linux_host_collector` e seções específicas Linux. **Não enviar** o JSON Windows para o endpoint `/collector/v1/servers/{server_id}/observations`: será rejeitado pela validação de domínio e precisa de extensão versionada e testada.
- Inventário Windows conhecido por referência de projeto: `SRV-PROTHEUS02` aparece em contexto operacional, mas nome, papel efetivo, autorização e cadastro atual exigem confirmação no host/Portal. **Não inferir inventário completo de nomes no repositório**.
- Escopo somente servidores, unidades 01/02. Não fazer descoberta indiscriminada de rede, não importar GLPI de estações e não alterar infraestrutura Sophos.

## Fase 1: diagnóstico local, SEM escrita e SEM rede

Arquivo: `it-portal-api/collectors/windows_host/Collect-ItPortalWindowsInventory.ps1`.

Em **um Windows Server aprovado**, executar PowerShell 5.1+ (conta normal com leitura WMI/CIM, sem elevação obrigatória):

```powershell
Set-Location C:\caminho\aprovado\delpi-central
& .\it-portal-api\collectors\windows_host\Collect-ItPortalWindowsInventory.ps1 -ServiceNames 'EventLog','W32Time','LanmanServer'
```

A saída é JSON no console. **Não publicar o JSON integral em GitHub, chamados ou chat**: contém identificador técnico do host, IPs, SO e configuração. Revisar campos e compartilhar somente evidências minimizadas por canal autorizado. O script não usa WinRM, não conecta a outros hosts, não modifica configuração, não grava arquivos, não transmite nem coleta senhas, argumentos de processos ou variáveis de ambiente.

Cobertura: hostname; hash SHA-256 de UUID de hardware **quando disponível** (não usar hash como autenticação); versão do SO; fabricante/modelo; CPUs lógicas e amostra de uso; uptime; total/memória disponível; volumes locais; endereços nas interfaces locais; status de nomes de serviços explicitamente permitidos. Dados CIM inacessíveis são marcados como `unavailable`/`partial`.

## Gate de inventário de servidores

Para cada Windows: registrar *somente após evidência*: hostname normalizado, unidade (01/02), função/criticidade, SO, IP(s) local(is), hipervisor/modelo, owner, serviços de negócio explícitos, registro preexistente no Portal, controles EDR/Zabbix/Windows e permissão de coleta. Identificar possíveis homônimos/VMs clonadas antes de conciliar; não criar servidores a partir de endereço IP isolado.

## Fase 2: integrar Windows ao Portal (proposta na E4.S3; ainda não implantada)

1. Contrato aditivo na API: `windows_host_collector`, chaves `cpu_usage_percent`, `uptime_seconds`, `windows_services` e estados de seção Windows; permitir apenas campos explícitos, sanitizar profundamente e impor limites por lista/tamanho. Preservar o contrato Linux.
2. Testes positivos/negativos: JSON realista do PowerShell, segredos aninhados, host incorreto, UUID divergente, replay `run_id`, allowlist de servidor/cliente, falha S2S, dados curados intactos.
3. Bindings de cliente S2S e servidor alvo com ACL específica; credenciais de coleta segregadas e sem logs; emissão Keycloak HTTPS e ingestão para gateway interno autorizado. Nunca reutilizar token humano ou abrir rota pública.
4. Frontend: CPU, RAM, disco, uptime, serviços Windows e data da última amostra, com indicação `partial`, `stale`, `unavailable`. O histórico atual de snapshots é inventário, **não** série temporal de desempenho.
5. Agendamento Windows Task Scheduler somente após smoke do coletor em um único servidor, revisão de segurança e autorização de operação. Serviço executa sob conta de serviço com mínimo privilégio e arquivos/venv/scripts não editáveis por essa conta.
6. Monitoramento posterior: projetar séries temporais com retenção/downsampling, intervalos adequados e regras de alerta; falha de ingestão não deve equivaler automaticamente a host offline. Priorizar SQL Server/Protheus e integrações industriais.

## Critérios de aceite desta fatia

- [x] Diagnóstico Windows versionado, sem rede nem escrita
- [x] Plano de coleta e restrições documentados
- [x] Execução e evidência de diagnóstico local em Windows Server 2019 (status complete; 7/7 seções ok)
- [ ] Testes automatizados PowerShell no Windows 5.1/7 (execução manual validada no Server 2019)
- [ ] Integração de fonte Windows na API e UI (código em PR E4.S3; aguarda merge/deploy/aceite)
- [ ] Homologação S2S, agendamento e monitoramento
