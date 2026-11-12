# #1576 P1 — Inventário completo Windows SCM (review-only)

## Escopo
Branch: feat/1576-windows-services-inventory-readonly. Sem deploy, sem execução
nos servidores e sem alteração da coleta E4.S3/E4.S4 existente.

Nova coleta local PowerShell 5.1+ de todos os Win32_Service (máximo 5000),
com lotes de até 100 serviços. Exclui PathName, StartName, ProcessId,
argumentos, segredos e qualquer operação de Start/Stop/Restart.

## Contrato dedicado (não é a observação de métricas V004/V005)
- POST /collector/v1/servers/{server_id}/host-services/batches
- scope Keycloak exclusivo: it-portal.host-services.ingest, audience it-portal-api.
- S2S por client_credentials, allowlist global do servidor e binding Windows
  por client_id + server_id já empregados pelo Portal. Novo client por host
  recomendado, sem reutilizar tokens humanos ou o scope legado.
- run_id UUID, observed_at ISO-8601 com timezone, host_identity.hostname,
  schema_version=1, batch_index 0-based, batch_count 1..50 e 1..100 services.
- Campos aceitos em cada serviço: name, display_name, description (até 500),
  state, start_mode, can_stop. Não aceita campos extras.
- O envio é idempotente por run_id+batch_index+hash; reenvio divergente resulta
  409, lote ausente não consolida, nomes repetidos entre lotes resultam 409.
- Coleta mais antiga ou de mesmo instante não substitui o estado atual.
- O inventário do servidor só muda em transação após todos os lotes chegarem.
- Serviços ausentes passam a is_present=false, nunca são apagados do cadastro;
  coleta parcial não marca ausências.
- Tabelas V006: host_service_runs, host_service_batches,
  host_services e host_service_current. Não altera cadastros E1/E2.

## Consulta humana
GET /servers/{server_id}/host-services com autorização
it-portal.access + it-portal.servers.view, filtros q/state/start_mode/present
e paginação de 1 a 100. Não oferece qualquer endpoint de controle.

## Frontend
Servidores > detalhe > Serviços Windows: somente visualização, última coleta,
busca, filtros, paginação e estado/presença. Se não houve uma coleta completa,
a interface comunica explicitamente ausência de dados.
Não confundir com "Serviços" do cadastro manual E2A.

## Gates e testes antes do merge
1. Testes: cd it-portal-api && python -m pytest -q
2. Banco Postgres isolado: migration V006, ingestão multi-batch,
   replay, concorrência, stale, falha parcial e preservação V004/V005.
3. Frontend: cd plugins/it-portal && npm test && npm run lint && npm run build.
4. PowerShell 5.1 no Windows em diagnóstico local sem envio:
   revisão de dados reais, caracteres, sigilo, compatibilidade,
   cobertura de todos os serviços, desempenho e limites.
5. Security review: validar provisionamento de scope e client S2S segregado;
   confirmar só URLs HTTPS autorizadas; instruções e segredos fora de Git.
6. Operação: não copiar nem executar scripts no SRV-DB01 ou outros hosts,
   não alterar Task Scheduler ou Keycloak sem liberação de implantação.
7. Merge e deploy exigem autorização explícita em fase posterior.

## Riscos residuais e decisões
- Limite de 5000 serviços por run, 50 lotes. Inventário maior deve ser
  tratado por revisão de contrato em vez de truncamento silencioso.
- Run incompleta e hashes de runs finalizadas permanecem no banco. Definir
  retenção operacional de runs antes de habilitar rotina recorrente.
- Serviço com descrição sensível deve ser mascarado na origem, nunca enviado
  para fora do host; a API também rejeita padrões sensíveis conhecidos.
- Não existe ainda uma tarefa agendada para esta coleta; os scripts novos
  são manuais e separados dos scripts de observações.
- Este P1 não concede controle de serviços e não constitui homologação de
  operação remota, disponibilidade ou continuidade do REST industrial.
