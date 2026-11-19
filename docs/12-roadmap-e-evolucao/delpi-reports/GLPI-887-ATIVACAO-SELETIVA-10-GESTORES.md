# GLPI #887 | Ativação seletiva de 10 gestores

## Autorização funcional de 19/11/2026

Auditoria final do ambiente informado pelo responsável:
- 12/12 gestores com e-mail verificado, conteúdo HTML e agenda semanal correta;
- todos os horários segunda-feira 09:00 America/Sao_Paulo;
- 0 e-mails enviados pela auditoria;
- gate global ainda OFF.

**Ativar SOMENTE** estas matrículas oficiais:

| Matrícula | Gestor |
| --- | --- |
| `10008` | JOICI MOTTA |
| `10257` | DENNIS GIORGIO PICCOLI |
| `10420` | MAX ULIANO LEMOS |
| `10500` | JOSE CARLOS DE LIMA JUNIOR |
| `10728` | MARCIA CRISTINA DE ABREU |
| `20001` | FABIANO SCHMITZ |
| `20002` | SONIA DE BORBA SCHMITZ |
| `20200` | MATHEUS SCHMITZ |
| `20410` | YURI BARBEITO COSTA |
| `PJ - 004` | JUNIOR CESAR PEDERSETTI |

**NUNCA ativar nesta operação**:
- `20057` | ALESSANDRA GAVA ROCHA;
- `20077` | IVONE SILVA DA ROCHA.

O script `app.scripts.glpi_887_activate_approved_managers` mantém
essas duas agendas `enabled=false` e nunca as escreve, inclusive no
modo `--apply`. Não envia e-mails.

O gate global `REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED` é uma autorização
da API como um todo, **não** um filtro de gestores. Quem determina qual
gestor recebe automaticamente é `enabled` na agenda individual,
com checagem de destinatário único e RH↔Core no momento do envio.
A liberação do gate passa a permitir disparos manuais autorizados no
sistema; não confundir com habilitar todas as agendas.

**Alteração de horário solicitada:** os 10 gestores aprovados passam a ser
configurados para segunda-feira às **09:00**. Agendas já preparadas
às 08:00 são migradas pelo ativador para 09:00; agendas já ativas
às 09:00 são preservadas sem ressetar o próximo disparo.
As matrículas excluídas `20057` e `20077` permanecem
**desligadas**, sem alteração das agendas.

## Pré-flight após merge

Conferir CI da PR e o checkout antes de qualquer deploy:

```bash
cd /home/operador/projetos/delpi-central
git status --short
git pull --ff-only origin main
bash ./infra/scripts/up-prod-sequential.sh --dry-run --fase core --build api-delpi
bash ./infra/scripts/up-prod-sequential.sh --fase core --build api-delpi
```

**Não** reiniciar outros serviços. A imagem da API Delpi é atualizada
para conter o novo script. Não há alterações de modelo de dados
nem migrations.

### 1. Prévia (LEITURA; nenhum envio ou gravação)

```bash
docker exec delpi-api-delpi python -m app.scripts.glpi_887_activate_approved_managers
```

Deve identificar `expectedManagers=12`, `approved=10`,
`excludedRegistrations=["20057","20077"]`,
`stillToEnable=10`, `currentlyEnabled=0`,
`excludedDisabled=true`. Se houver divergência,
**não prossiga**.

### 2. Habilitar autorização de envio na API Delpi

A autorização dos 10 gestores é explícita. Editar SOMENTE a linha
seguinte no arquivo de infraestrutura de produção `infra/.env`:

```env
REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED=true
```

Não colar o conteúdo do arquivo `.env` em logs, PR ou mensagens.

Recriar **somente** o serviço API Delpi (não precisa rebuild de
imagem: a variável vem do Compose e muda no recreate):

```bash
bash ./infra/scripts/up-prod-sequential.sh --dry-run --fase core api-delpi
bash ./infra/scripts/up-prod-sequential.sh --fase core api-delpi
```

Confirmar a variável **dentro do container de produção** e status:

```bash
docker exec delpi-api-delpi python -c "from app.config import settings; print('GATE_ATIVO:',settings.REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED)"
docker ps --filter name=delpi-api-delpi
```

Se `GATE_ATIVO` não for `True`, não execute `--apply`.

### 3. Ativar SOMENTE as 10 agendas autorizadas

```bash
docker exec delpi-api-delpi python -m app.scripts.glpi_887_activate_approved_managers --apply --confirm ATIVAR_10
```

O script confirma a árvore RH raiz `10257`, **exatamente 12
matrículas**, mapeamentos Core prontos, destinatário único
e idêntico ao Core/RH, equipes diretas do provider, definições
ativas, ausência de `weekStart` fixo, cron semanal segunda
09h, fuso correto e as duas exclusões desligadas.

Qualquer divergência bloqueia antes de alterar. Em falha de
gravação no meio, a operação pode ficar parcial; auditar o
estado atual antes de repetir. Não duplicar disparos:
o script não executa o envio nem chama processamento de agendas.

### 4. Conferência final (LEITURA)

```bash
docker exec delpi-api-delpi python -m app.scripts.glpi_887_activate_approved_managers
```

O esperado:
- `approved=10`
- `currentlyEnabled=10`
- `stillToEnable=0`
- `excludedDisabled=true`
- `deliveryGateEnabled=true`
- Todos os próximos horários dos aprovados devem estar no futuro,
  segunda-feira às 09h `America/Sao_Paulo`.

Além disso, validar o poller interno:

```bash
docker logs --tail 120 delpi-api-delpi | grep -E 'reports_schedule_poller_(started|tick|failed)'
```

`REPORTS_SCHEDULE_POLL_SECONDS` deve ser positivo (900 s por padrão).
Sem outro cron host ativo que dispare a mesma coisa; o claim
atômico do banco reduz duplicidade, mas a observabilidade é útil.
Não executar `process-pending` manualmente para testar depois de
liberar as agendas, pois ele envia relatórios vencidos de verdade.

**Primeiro envio recorrente previsto:** 23/11/2026,
segunda-feira, 09h de Brasília, sujeito ao poller (até 15 min de
atraso no padrão e disponibilidade do serviço). O e-mail deverá
abranger 16/11–22/11/2026, a semana completa anterior.

## Se precisar suspender o disparo

Para interromper imediatamente novos envios da família de
relatórios, definir `REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED=false`
e recriar somente `api-delpi`. Atenção: agendas individuais
continuarão `enabled=true`; se o poller processá-las com o gate
OFF, os próximos horários podem avançar sem entrega. Na retomada,
audite `nextRunAt` e reabilite conscientemente. Preferir desativar
as 10 agendas individualmente antes de desligar a chave, quando
operacionalmente possível.

## Separação de responsabilidades

- **Cadastro e vinculação RH/Core:** independente de hierarquia,
  com confirmação manual e auditoria.
- **Descoberta de gestores:** Portal RH, raiz `10257`.
- **Relatórios:** somente subordinados **diretos**, consentimento
  `usage_tracking`, nunca presumir falta de dados como uso zero.
- **Entrega:** e-mail exclusivamente ao destinatário verificado.
- **Exclusões:** `20057` e `20077` permanecem desligadas.

### Testes

```bash
cd api-delpi
pytest tests/test_glpi_887_activate_approved_managers.py -q
```

Nenhum deploy, modificação de `.env` ou ativação de agenda são
executados automaticamente pelo merge desta PR.
