# DECISOES_FUNCIONAIS_PENDENTES

Só o que o **repositório não responde**. Não bloqueia o desenho do Portal.

| ID | Pergunta | Por que o git não fecha | Impacto | Subetapa |
|----|----------|-------------------------|---------|----------|
| P-01 | URLs, ids e tipo (iframe/PBI/Sheets) dos 6 apps do PO | Códigos `*.access` ausentes do monorepo | Redirects, paridade, menu | E1.S1 |
| P-02 | Comprador ES existe no Core? | Evidência PO só SC | Papéis e unit-02 | E1.S2 |
| P-03 | Regra do BI Atraso SC = OTD nativo? | Sem SQL/relatório no git | WF-07 paridade vs MANTER_EXTERNO | E1.S1 + E9.S1 |
| P-04 | Regra do BI Controle Estoques SC | Idem | WF-15 | E1.S1 + E7 |
| P-05 | Existe processo de importação no TOTVS já mapeado? | Zero rota import no OpenAPI supplies | WF-08 P1 ou BLOQUEADO | E1.S1 |
| P-06 | Alçada: UI de `C7_APROV` basta ou o BI tem workflow? | Contrato diz que C7_APROV não é status operacional | P1 alçadas | E1.S3 |
| P-07 | Quem edita a planilha IDD e se o app Sheets deve permanecer | Perm `idd-suprimentos.access` só no PO | MANTER_EXTERNO vs só leitura Portal | E1.S1 |
| P-08 | Cobertura no Overview: meses de giro **ou** cobertura ESTSEG? | Dois conceitos no código | KPI-COVERAGE bloqueado | E1.S3 (workshop KPI) |
| P-09 | Threshold aging SC (`due_soon`) | Contrato 0.2 deixou em aberto | Worklist buckets | E13 + homolog SC |
| P-10 | Janela de freeze da purchase-requests-api na C2 | Sem métrica de rows/jobs em prod neste doc | Dual-read | E6.S4 |
| P-11 | Projeção Qualidade no 360: quais campos o comprador pode ver (RBAC cruzado)? | inspecoes tem perms próprias | Não vazar inspeção sem cap | E10.S3 |
| P-12 | Assinatura formal das fichas KPI (owner nomeado) | Helps confirmam comportamento código, não dono de negócio | Status PARCIAL | E1.S3 |

**Fechado pelo PO (2026-09-08):** modelo de unidade = eixo B `supplies.unit.filial-{TOTVS}`, sem inflar capabilities — [ADR-006](./adr/ADR-006-unit-permissions.md). P-02 continua só sobre *existência* do papel Comprador ES no Core, não sobre o modelo.

Enquanto P-01 não fecha: **proibido** inventar `app id` ou redirect.
