# GLPI #1178 — Alerta diário de estoque abaixo da segurança

**Solicitação:** Fabiano Schmitz, Delpi Reports. O relatório abaixo é **preventivo**
e não substitui o relatório de ruptura de estoque projetada nos próximos 30 dias.

## Regra de negócio e fontes

| Campo | Fonte / regra |
|---|---|
| Filial | Uma definição `01` (SC) ou `02` (ES), não há agregado misto |
| Código e descrição | SB1, universo oficial do Estoque de Segurança (MP ou prefixo 3019) |
| Saldo físico disponível | SB2 B2_QATU dos armazéns **01 + 98 + 99** |
| Estoque de segurança | SBZ BZ_ESTSEG da filial |
| Déficit | `max(0, estoque de segurança − saldo 01+98+99)` |
| Produto em alerta | ESTSEG > 0 e saldo estritamente menor que ESTSEG; bloqueados excluídos |
| Pedido aberto | SC7, `C7_QUANT > C7_QUJE`, residual diferente de S, filial vinculada |
| Pedido / quantidade | C7_NUM, C7_ITEM, quantidade **em aberto** C7_QUANT − C7_QUJE |
| Data prevista | C7_DATPRF (vencida ou vazia sinalizada) |
| Elegibilidade | Armazém de destino 01/98/99 + unidade compatível/convertível |
| Cobertura | `saldo_atual + Σ(qtd_aberta_elegível) >= ESTSEG` |
| Frequência | `weekdays`, seg–sex em America/Sao_Paulo, sem calendário de feriados |

O e-mail exibe os pedidos abertos encontrados inclusive os de armazém
ou UM não elegível, identificando expressamente que não participam da cobertura.
`sufficient` = atende o **volume** do estoque de segurança; `partial` =
há pedido elegível, mas insuficiente; `none` = não há cobertura elegível.
Uma entrega prevista não é garantia de disponibilidade na data. Mesmo que
a soma de pedidos atenda em quantidade, as previsões vencidas/sem data
são destacadas.

O objetivo do chamado é atuar antes da ruptura. Entretanto, como um saldo
zero também está **abaixo do estoque de segurança**, ele permanece no alerta,
separadamente identificado como **sem saldo**. Não confundir com o cálculo de
ruptura projetada por empenhos SD4.

As consultas existentes em `SafetyStockQueryRepository` são reutilizadas,
sem reescrever as regras de SBZ/SB2/SC7 nem fazer N+1 de detalhes.

## Como disponibilizar após revisão e merge

1. Verificar o checkout de produção e fazer pull fast-forward da `main`.
2. Reconstruir somente `api-delpi` e o microfrontend `reports`.
3. Abrir `https://minhadelpi.com.br/apps/reports` → **Novo relatório**.
4. Escolher **Alerta diário — abaixo do estoque de segurança**.
5. Criar **uma definição para 01 / SC** e outra **para 02 / ES**.
6. Em cada definição, selecionar e **salvar os destinatários reais** no diretório,
   verificar a pré-visualização e salvar a agenda `Dias úteis (seg–sex)`,
   fuso `America/Sao_Paulo` e horário apropriado (ex.: 08:00).
7. Manter a agenda desabilitada até destinatários e conteúdo aprovados. Depois,
   habilitar, fazer um envio manual de homologação e acompanhar histórico de
   execuções e entregas via Reports. O worker `process-pending` deve estar
   efetivamente agendado no host; apenas criar o cron não garante execução.
8. Validar saldos e PCs para ambas as filiais e ausência de mistura de dados.

### Pull, dry-run e deploy

```bash
git status --short
git switch main
git pull --ff-only origin main

bash ./infra/scripts/up-prod-sequential.sh --dry-run --build api-delpi
bash ./infra/scripts/up-prod-sequential.sh --dry-run --fase mfe --build reports

# Somente depois de inspecionar o plano:
bash ./infra/scripts/up-prod-sequential.sh --build api-delpi
bash ./infra/scripts/up-prod-sequential.sh --fase mfe --build reports
```

O uso de `bash` evita o erro `Permission denied` do script sem bit de
execução (o arquivo precisa, ainda assim, ser legível). Não usar sudo
indiscriminado. Sem migration ou mudança de dados no ERP.

### Testes

```bash
cd api-delpi
python -m pytest tests/test_glpi_1178_safety_stock_below_daily.py   tests/test_safety_stock_shortage_30d_provider.py   tests/test_report_schedule_and_run.py   tests/test_reports_routes_smoke.py -q

cd ../plugins/reports
npm ci
npm run lint
npm run build
```

**Não houve criação automática de agendamentos/destinatários** nesta PR,
e nenhum envio por e-mail é realizado ao fazer merge.
