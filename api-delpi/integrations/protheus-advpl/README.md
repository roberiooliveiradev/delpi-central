# Integrações ADVPL Protheus — workspace DELPI

**Decisão de escopo (PO):** todos os fontes ADVPL/TLPP *candidatos* produzidos pela DELPI para novas integrações ficam versionados **neste repositório**, em `api-delpi/integrations/protheus-advpl/`. **Não modificar nem publicar** no repositório da equipe ERP `Delpi-ti/protheus-erp` durante esta fase. Aquele repositório é fonte de consulta versionada para dependências/customizações, não destino dos nossos commits.

**Responsabilidade:** workspace de entrega de fontes + contratos e manifestos; não é um runtime de API Python, serviço REST ativo, RPO ou autorização para compilar. A API Python permanece em `api-delpi/app/` sob suas camadas existentes e a integração é por contratos oficiais, nunca por import do código ADVPL.

## Organização-alvo (criar paths sob demanda)

```text
api-delpi/integrations/protheus-advpl/
  README.md
  modules/
    product-master/
      src/          # DLP04I01.PRW candidato; não copiar legado automaticamente
      contracts/    # versões de REST, JSON, erros, campos, owners
      tests/        # fixtures e verificações estáticas; sem ERP write
    product-suppliers/
      src/          # DLP04I02.PRW = nome sugerido, verificar colisão antes de usar
      contracts/
      tests/
  shared/           # apenas após Abstraction Gate e 2+ consumers reais
  packaging/        # scripts determinísticos para montar pacote imutável
  handoffs/         # manifestos SHA-bound e comprovantes, nunca ZIPs mutáveis
```

Organizar por **capacidade de negócio**, não por HTTP verb. Cada módulo possui suas rotas, contratos e testes; não importar fontes de outro módulo. Utilitários compartilhados somente com owner, consumer, necessidade e testes reais. `openai-plugin/` é integração independente e não deve ser alterada.

## Primeira entrega — PRC SB1 / SA5

- `product-master`: REUSE/EXTEND `DLP04I01.PRW` (upstream `DELPIPRODUTO`, MATA010/ExecAuto), preservando contratos publicados. CREATE/UPDATE já têm fonte; operações adicionais exigem inventário/contrato e autorização.
- `product-suppliers`: avaliar primeiro submodelo `Model061` em `MATA010M_DLP.PRW` e o `Dmata061.prx` MVC antes de NEW; fachada REST SA5 candidata independente, somente após ratificação do modelo, identidade completa e operações suportadas.
- **DELETE:** nunca implementar sem semântica ERP aprovada. **READ:** reutilizar API DELPI existente quando adequado; read-back SA5 precisa chave integral.
- Cobertura de CRUD = operações de negócio contratadas, não exposição indiscriminada dos campos físicos.

## Fontes e evidência

1. **Fonte de referência da equipe ERP:** `Delpi-ti/protheus-erp`, `master`@SHA; registrar caminho e blob SHA de cada rotina estudada. Não efetuar escrita nesse repositório.
2. **Workspace autoral deste projeto:** fontes novos/evoluídos em `modules/*/src/`, versionados pelo SHA do `delpi-central`. Cada arquivo deve ter provenance da base original, licença/permissão aplicável, mudanças DELPI e status `SOURCE_CANDIDATE`. Não sobrescrever o espelho histórico `docs/13-fontes-totvs-protheus/`.
3. **Biblioteca canônica de regras:** `api-delpi/docs/api/padroes-totvs/` e `api-delpi/docs/integrations/`; manter um único contrato por capacidade.
4. **Runtime:** RESTALL indica rota publicada, SX3 indica metadados, RPO/compilação/homologação com owner ERP comprova versão em execução. Fonte GitHub não prova deploy.

## Versionamento e pacote de compilação

- Cada entrega fixa **SHA do delpi-central**, `source_repo/ref/sha/path/blob` de dependências, hashes SHA-256 dos fontes/contratos, lista de arquivos, contrato API, mudança e rollback, permissões e versão do pacote.
- Rótulos de estado: `SOURCE_CANDIDATE → SOURCE_REVIEWED → COMPILATION_PENDING → TST01_COMPILED → TST01_VALIDATED → PRD_APPROVED → PRD_PUBLISHED`. Nenhuma promoção por inferência.
- `packaging/` futuramente gera ZIP determinístico **a partir de um commit aprovado**, com `manifest.json`, `fontes/`, `contratos/`, `homologacao/`. ZIP é artefato de distribuição, não fonte de verdade e não é mantido como cópia divergente no Git.
- `handoffs/` guarda a referência do artefato/issue, SHA-256 do ZIP, responsável, ambiente e resultado da equipe ERP. Separar pacote TST01 de promoção PRD sem duplicar código por ambiente.
- Configuração de destino **não** é hardcoded em `.PRW`: a equipe compila no RPO/ambiente escolhido; API DELPI aplica feature gate default OFF e pin fail-closed, ver `protheus-write-integration-playbook.md`.

## Gates e ownership

Keycloak = identidade; Core = AuthZ/RBAC; `api-delpi` = integração; Engenharia = workflow PRC; equipe ERP = compilação/publicação/rotinas e regras oficiais. Sem SQL/RecLock direto no ERP. Nunca executar ERP write, RPO compile ou deploy por consequência de commit de fonte/documentação. Se `AGENTS.md` exigir deploy geral, resolver conflito de escopo com owner **antes** de ação que afetaria runtime.

**Próxima tarefa permitida:** criar módulos/contratos e primeiros fontes candidatos em `modules/`, com revisão técnica e testes estáticos; a compilação TST01 depende de aprovação/handoff separado.
