# Divergência ROL × relatório Protheus — diagnóstico

Parte da [biblioteca de padrões TOTVS](./README.md).

Procedimento canônico para investigar diferença entre o ROL/faturamento do
Minha DELPI e relatórios do Protheus (ex.: "Resumo de Vendas" customizado).

Regra canônica do ROL: `CommercialRolReturnSql`
(`app/domain/services/commercial/commercial_rol_return_sql.py`) +
`FinancialRepository.get_rol()`. Ficha de negócio: `KPI-ROL` em
[KPI-FICHAS.md](../../../../docs/12-roadmap-e-evolucao/commercial/KPI-FICHAS.md).

---

## Regra em resumo

```text
VLR_VENDA  = Σ SD2 (D2_TOTAL − D2_VALICM − D2_VALIMP5 − D2_VALIMP6)
             por D2_EMISSAO + filial, somente linhas elegíveis
VLR_DEVOLUCAO = Σ SD1 (mesma expressão) por D1_DTDIGIT,
             CF 1201/2201 ou D1_TIPO='D' com TES F4_DUPLIC='S'
ROL        = VLR_VENDA − VLR_DEVOLUCAO
```

Elegibilidade SD2 (pontos que mais explicam divergência):

- `D_E_L_E_T_ = ''`; `D2_TIPO <> 'D'`; `A1_NOME` preenchido.
- TES com `F4_DUPLIC = 'S'` (padrão) — exclui remessas/retornos de
  industrialização, transferências de produção e amostras (famílias TES
  524/525/534/540/541/550/551/590…, CFOP 5902/6902/6903/6151/59xx).
- Exceções: CFOP `5927` "BAIXA ESTOQUE" (MI) com devolução associada; CFOP
  `5911`/`6911` produto `90%` UM `MI` na filial `01`.

## Incidente de referência — Helpdesk #0001164 (set/2026)

Período 01–25/09/2026, filial 01:

| Medida | Minha DELPI | Relatório customizado Protheus |
|--------|-------------|-------------------------------|
| Vendas líquidas | 810.514,05 | 851.236,88 |
| Devoluções | 2.460,89 | 2.460,89 |
| ROL / Total | **808.053,16** | **848.775,99** |

Diferença: **R$ 40.722,83** — WEG `+21.920,20`, Novos Negócios `+18.802,63`.

Reconciliação documental (consulta read-only no TOTVS, mesmo banco da API):

- O delta de Novos Negócios corresponde exatamente à NF **102803**
  (FLEXTRONICS `000273|01`, CFOP `6903`, TES `524` "retorno de mercadoria
  recebida p/ industrialização não aplicada" — material do próprio cliente).
- O delta de WEG concentra-se na loja `01` em itens de remessa/retorno de
  beneficiamento (CFOP `5902`, TES `525`), mesma natureza.
- Filial `02` sem divergência: não havia esse cenário no período.

**Causa validada pela equipe Protheus:** o relatório customizado incluía
**materiais de terceiros** (materiais do próprio cliente usados no
beneficiamento) na composição do valor líquido de faturamento. Esses itens
não são receita; o Minha DELPI já os excluía pela regra de elegibilidade.
Correção ficou a cargo do consultor Protheus no relatório customizado.

**Pendente:** evidência de que, após a correção do relatório, o total
passou a coincidir com o Minha DELPI.

## Procedimento para futuras divergências

1. Confirmar que período, filial e demais filtros são equivalentes nos dois lados
   (atenção: `competence` na URL do Portal **não** entra na query do ROL; o
   recorte efetivo é `start_date`/`end_date` sobre `D2_EMISSAO`).
2. Obter o **valor exato** e, preferencialmente, o **extrato** do relatório
   Protheus usado na comparação.
3. Reproduzir o cálculo da rota Minha DELPI com consulta **read-only** na
   fonte TOTVS, sem alterar código — a query canônica já provou reproduzir o
   valor da tela ao centavo.
4. Separar vendas, impostos/descontos, devoluções e ROL final; localizar em
   qual componente a diferença nasce.
5. Decompor por cliente+loja e por documento (NF/série/item, CFOP, TES,
   `D2_TIPO`, UM) — comparar a população elegível do Portal com a população
   do relatório.
6. Verificar especificamente itens de **materiais de terceiros /
   beneficiamento** (ver [materiais-terceiros-sb6.md](./materiais-terceiros-sb6.md)):
   o relatório pode estar contando remessas/retornos de material do cliente
   como faturamento.
7. Só então classificar qual lado diverge da regra de negócio esperada.

## O que NÃO fazer

| Anti-padrão | Por quê |
|-------------|---------|
| Assumir "se diverge do Protheus, o Protheus está errado" | Conclusão válida **só** para o incidente #0001164; não há prova generalizável |
| Ajustar a query do Portal para "fazer o número bater" | Esconde divergência real de critério; corrompe a regra homologada |
| Tratar remessa/retorno de beneficiamento como venda | Não gera duplicata nem receita — o incidente validou isso |
| Comparar totais sem extrato | Só a reconciliação documento a documento prova a causa |

## Referências

- `CommercialRolReturnSql` — `app/domain/services/commercial/commercial_rol_return_sql.py`
- `FinancialRepository.get_rol` — `app/infrastructure/persistence/totvs/financial_repositories/financial_repository.py`
- Alinhamento ao "Resumo de Vendas": commit `0876c8d35e` (25/05/2026); refinamento de devoluções: `a48f663f06` (28/08/2026)
- Ficha `KPI-ROL`: [KPI-FICHAS.md](../../../../docs/12-roadmap-e-evolucao/commercial/KPI-FICHAS.md)
- Materiais de terceiros: [materiais-terceiros-sb6.md](./materiais-terceiros-sb6.md)
- Chamado Helpdesk **#0001164**
