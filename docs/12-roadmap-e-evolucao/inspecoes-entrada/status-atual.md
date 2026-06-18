# Status atual — Inspeções de Entrada

> Snapshot em **2026-06-18**. Roadmap completo: [ROADMAP.md](./ROADMAP.md)

## Resumo

| Camada | Status |
|--------|--------|
| Views TOTVS `vw_minha_delpi_inspecoes_entrada_*` | ✅ Script Fase 0 disponível |
| API api-delpi (7 rotas GET) | ✅ Implementada + testes |
| MFE `inspecoes-entrada` | ✅ Dashboard + histórico + detalhe |
| Docker compose dev | ✅ Serviço `inspecoes-entrada` |
| Core API register + RBAC prod | ⏳ Pendente |
| Script CI/homologação | ⏳ Pendente (`check-inspecoes-entrada.sh`) |
| Chat / apresentação operacional | ⏳ Fora do escopo v0.1 |
| UI rejeitadas por ensaiador | ⏳ API pronta, painel não implementado |

## O que já funciona

### Backend (api-delpi)

- Resumo por filial (`/resumo`) com KPIs e tempo médio
- Pendências paginadas (`/pendentes`) com descrição de produto (SB1)
- Ranking fornecedor (`/pendentes-fornecedor`)
- Rejeitadas por produto (`/rejeitadas-produto`) e por ensaiador (`/rejeitadas-ensaiador`)
- Histórico filtrado paginado (`/historico`)
- Detalhe com ensaios QER (`/historico/detalhe`)
- RBAC por filial + envelope `meta` (Playbook 10)
- Suite de testes unitários e smoke de rotas

### Frontend (MFE)

- Rotas por filial (`filial-01`, `filial-02`) com menu separado no manifesto
- Abas **Visão geral** e **Histórico** (`?tab=historico`)
- Cards KPI, gargalos por fornecedor, produtos rejeitados, tabela de pendências
- Histórico com filtros (resultado, datas, fornecedor, produto, ensaiador, NF, lote)
- Modal de detalhe com cards de ensaio e impressão de certificado
- Design alinhado ao portal (`ie-` prefix, tokens CSS, responsivo)
- Header `X-Delpi-Caller-App: inspecoes-entrada`

## Avaliação técnica (branch atual)

### Pontos fortes

- **Clean architecture** respeitada: port → repository → use case → router → composer
- **Contrato api-delpi** completo (`api_delpi_success`, `route_contract_registry`, OpenAPI agent metadata)
- **Cobertura de testes** ampla no backend (use cases, rotas, SQL filtros)
- **Separação por filial** coerente com outros plugins (auditoria-5s, central-agendamento)
- **Detalhe de ensaios** com regra explícita de medição (QES > QEQ, sem inventar valores)

### Lacunas / riscos

1. **Registro na Core API** ainda manual — plugin não aparece no menu até `register-manifest.sh`
2. **Endpoint `/rejeitadas-ensaiador`** sem consumidor no MFE (dados disponíveis só via API)
3. **Pendências no dashboard** limitadas a 200 registros (`PENDING_DASHBOARD_PAGE_SIZE`) — filial com volume maior pode truncar sem aviso explícito
4. **Sem script de homologação** no padrão `scripts/homologacao/check-*.sh`
5. **Sem integração chat** (registry operacional, perfis apresentação) — esperado para fase posterior
6. **Views TOTVS** dependem de deploy DBA — validação Fase 0 deve rodar em cada ambiente

## Bloqueios para produção

1. Manifesto não registrado na Core API do ambiente alvo
2. Perfis sem permissão `inspecoes-entrada.view.*`
3. Views TOTVS não publicadas ou divergentes do contrato documentado
4. Ausência de smoke automatizado no CI

## Próximo passo

1. **Fase 3** do [ROADMAP.md](./ROADMAP.md): registro portal, RBAC e homologação em staging.
2. Validar views com `validate_inspecoes_entrada_views.py` no ambiente alvo.
3. Avaliar paginação/limite da tabela de pendências no dashboard conforme volume real.
