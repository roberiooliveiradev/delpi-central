# E4.S3 — observações Windows no Portal de TI (piloto S2S)

**Estado:** código proposto em branch/PR; **não implantado**. Operação produtiva,
agendamento e aceite dependem de revisão e smoke manual. Não ativa tarefas.

## Escopo

- Usa o diagnóstico read-only E4.S2 (PowerShell 5.1+).
- Aceita `source=windows_host_collector` no contrato v1 da API, com **allowlist
  independente** para `summary` e `sections_status` Windows.
- Persiste na tabela V004 existente e exibe na ficha do servidor:
  SO, CPU lógica e utilização pontual, uptime, memória, volumes, NICs, serviços e
  data da amostra. Não sobrescreve inventário manual.
- Mantém os contratos Linux, histórico, idempotência de `run_id` e verificação
  de hostname. O histórico de snapshots **não é série temporal**.
- Fora de escopo: correção de espaço em disco, SQL backup, alertas, agendamento
  Task Scheduler, instalação remota, descoberta de rede, GLPI, alterações de
  firewall, WinRM e acesso privilegiado.

## Pré-requisitos de implantação (todos obrigatórios)

1. Confirme que o Windows Server piloto já existe no cadastro do Portal de TI
   (não cadastrar duplicado) e anote o UUID do servidor. O `hostname` cadastrado
   **deve corresponder** ao hostname local normalizado emitido pelo coletor.
2. No Keycloak, administre um **cliente confidencial exclusivo do Windows
   piloto**, com `client_credentials`, client scope
   `it-portal.observations.ingest` e audience `it-portal-api`.
   Não reutilizar o client ID/segredo Linux, nem JWT de usuário.
3. Em `infra/.env` do servidor da API, preservar os clientes/UUIDs Linux
   existentes e **acrescentar** o Windows:
   ```dotenv
   IT_PORTAL_S2S_ALLOWED_CLIENTS=it-portal-host-collector,it-portal-windows-pilot01
   IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST=<uuid-linux>,<uuid-windows>
   IT_PORTAL_WINDOWS_COLLECTOR_BINDINGS=it-portal-windows-pilot01=<uuid-windows>
   ```
   Os nomes/UUIDs acima são exemplos, não valores reais. Para mais de um Windows,
   separar bindings com `;` e criar um client S2S por host.
   **Bindings vazios = ingestão Windows negada**.
4. Fazer deploy `it-portal-api` e `plugins/it-portal` no procedimento
   habitual e conferir a versão de código antes de qualquer envio.
   Nenhuma migration adicional é exigida além de V004 já existente.

## Smoke manual no Windows Server (somente após deploy e Keycloak configurado)

Colocar **os dois arquivos** juntos numa pasta aprovada pelo time de TI:

- `Collect-ItPortalWindowsInventory.ps1`
- `Send-ItPortalWindowsObservation.ps1`

Comparar a origem com o repositório aprovado. Se houver marcador de internet,
removê-lo apenas para o arquivo revisado conforme `RemoteSigned` (não alterar
política de execução do host). Não colocar senhas nem tokens em arquivos/comandos.

No PowerShell 5.1+, executar **uma linha**, substituindo os placeholders.
O segredo será solicitado interativamente sem eco:

```powershell
& 'C:\CAMINHO\Send-ItPortalWindowsObservation.ps1' -ApiBaseUrl 'https://PORTAL-APROVADO/apps/it-portal-api' -S2sTokenUrl 'https://KEYCLOAK-APROVADO/realms/delpi/protocol/openid-connect/token' -ClientId 'it-portal-windows-pilot01' -ServerId '<uuid-windows>'
```

A URL da API deve ser o **gateway HTTPS autorizado**. O publicador não aceita
HTTP, não solicita permissões administrativas, não cria arquivo de estado e não
faz discovery de terceiros. O JSON é enviado somente após coleta local bem-sucedida.

**Aceite:**

- Resposta do publicador `status=enviado` e `run_id` sem revelar JSON/segredo.
- UI `Servidores → detalhe → Inventário automático` exibe
  `source=windows_host_collector` e CPU, RAM, discos, uptime e serviços.
- Consulta GET humana mostra observação `available` (ou `partial`
  para coleta parcial); divergências de cadastro não são aplicadas
  automaticamente. A anterior coleta Linux continua íntegra.
- Um segundo envio cria outro `run_id` novo. Reenvio de mesmo `run_id` na
  API é idempotente.
- Sem aprovação operacional, **não ativar Task Scheduler**.

## Diagnóstico de erro

- 401/403: Keycloak S2S, client, audience, escopo, URL do gateway.
- 409 `collector_allowlist_empty` ou `collector_server_forbidden`:
  UUID não autorizado pela allowlist global.
- 409 `windows_collector_binding_forbidden`: client ID e UUID não
  correspondem a `IT_PORTAL_WINDOWS_COLLECTOR_BINDINGS`.
- 422 `hostname_mismatch`: hostname local diferente do cadastro; reconciliar
  manualmente sem desabilitar a proteção.
- 422 `invalid_observation`: contrato/sanitização; não compartilhar JSON
  completo publicamente (contém configuração do host).

## Verificações do PR

```bash
cd it-portal-api
pytest -q tests/test_observations_domain.py tests/test_observations_http.py
cd ../plugins/it-portal
npm run build
npm test
```

**Limitação:** Testes de PowerShell 5.1 + integração real Keycloak/HTTPS e deploy
não podem ser declarados aprovados apenas com revisão de código. Exigem smoke
na infraestrutura autorizada.
