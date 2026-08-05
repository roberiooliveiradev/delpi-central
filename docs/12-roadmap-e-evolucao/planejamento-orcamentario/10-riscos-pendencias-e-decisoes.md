# 10 — Riscos, pendências e decisões

## 1. Divergências documentação × código

| Tema | Doc legado (`documentos/`) | Código / `docs/` atual |
|------|----------------------------|------------------------|
| Stack API | Flask | FastAPI (api-delpi e *-api) |
| Manifesto | Spec v2 / 1.1.0 | Schema **1.0.0** vigente |
| Inventário apps | CRM/GPT genéricos | Dezenas de MFEs + hub api-delpi |
| Permissões no JWT | Modelos teóricos variados | JWT identidade; RBAC via Core API |

## 2. Inconsistências nos materiais de orçamento

| ID | Evidência | Impacto | Recomendação | Decisão necessária |
|----|-----------|---------|--------------|-------------------|
| D1 | Arquivo `Carta Orcamento - 2027.doc` com texto de **2026** e prazo 04/11/2025 | Orientação errada no go-live | Nova Carta 2027 versionada no app | Negócio fornece texto oficial 2027 |
| D2 | Carta pede pessoal por **CC e cargo**; planilha só **área/unidade** | Modelo de dados bifurcado | MVP = planilha; roadmap cargo/CC | Qual é a fonte oficial 2027? |
| D3 | Carta cita campo **nacional/importado**; planilha CAPEX não tem coluna | Validação incompleta | Incluir campo se financiamento exigir | Obrigatório em 2027? |
| D4 | Contas CAPEX: lista fechada nas instruções vs valores livres na TI 2026 (SERVIÇOS, CAPACITAÇÃO…) | Regras de validação | Catálogo + “Outros” com justificativa | Lista estrita ou extensível? |
| D5 | Classificação Carta (produção/segurança/meio ambiente) vs Classif. 1–6 da planilha | Ambiguidade UX | Usar Classif. 1–6; uso em observações | Confirmar |
| D6 | Previsão de Receita **não encontrada** | Buraco de escopo | Fora do MVP ou spike | Entregar PPT/PDF |
| D7 | Pessoal 2027 todo zerado | Sem exemplos reais | Usar ciclo 2026 preenchido se existir | Há planilha preenchida? |
| D8 | Protótipo Desktop é outro domínio | Risco de reuso errado | Ignorar como base | — |
| D9 | Var. fórmulas Pessoal usam E/C e G/E; coluna OUTUBRO não entra na var | Regra de KPI | Replicar planilha no MVP | Confirmar intenção |

## 3. Pendências técnicas

| ID | Pendência | Bloqueia? |
|----|-----------|-----------|
| T1 | SELECT na view de CC / amostra ROL em homologação | Parcial (mestres) |
| T2 | Docker indisponível na sessão de descoberta | Não (docs ok) |
| T3 | Células numéricas do CAPEX `.xls` 2027 não parseadas sem xlrd | Baixo (SST+TI2026 bastam para modelo) |
| T4 | Definir slug final `planejamento-orcamentario` vs nome curto | Não |
| T5 | Volume Compose path final | Na implementação |

## 4. Riscos críticos

1. **Escopo receita** estourar o prazo se entrar sem especificação.
2. **Autorização CC** mal implementada → vazamento entre gestores.
3. **Reset de schema** plugins em prod (proibido) — treinar operadores.
4. **Carta desatualizada** minando compliance de confirmação de leitura.
5. Dependência de **cadastro manual de escopos** atrasar treinamento.

## 5. Registro de decisões de arquitetura (resumo)

| Decisão | Escolha | Doc |
|---------|---------|-----|
| Backend | Módulo api-delpi + postgres-plugins | `11-adr-backend.md` |
| Pessoal MVP | Shape da planilha (área) | `09` |
| Receita | Pós-MVP salvo material+decisão | `09` |
| Aprovação | 1 nível + Diretoria all | `04`/`05` |
