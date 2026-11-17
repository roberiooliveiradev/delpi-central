# ATLAS P2.2h.2bo-br | Cadeia one-shot HML candidata (somente codigo e CI)

**Data:** 17/11/2026 (BRT). **Estado:** Draft PR; sem instalacao/ativacao. **PREPARE/ACT:** OFF. **Decisao de arquitetura:** [issue #232](https://github.com/roberiooliveiradev/delpi-central/issues/232), ainda aberta.

## Contexto

PR #237 mesclada em `d1e23f930ff472cdc022288e500ae271358f4917` entregou um publicador atomico **somente de teste**; PR #236 havia entregue o leitor por descritor; PR #234 havia entregue o validador JSON. Agora o novo arquivo `atlas_hml_one_shot_candidate.py` conecta essas tres pecas com `HMLDockerInspectOnly` (GET unico HML) em uma rotina candidata **injetada em testes descartaveis**, nao uma unidade operacional.

## Fluxo testado

```text
[httpx.AsyncBaseTransport fornecido pelo teste]
       |
       v
[HMLDockerInspectOnly] - GET /containers/delpi-hml-public-hub/json
       |
       v
[RuntimeContainer tipado e sanitizado]
       |
       v
[build_hml_snapshot_claim] - 11 campos estritos e timestamp NAO atestado
       |
       v
[_publish_in_review_directory] - staging + fsync + rename em tmp_path
       |
       v
[atlas_hml_snapshot_file_reader] - somente leitura por FD
       |
       v
[status=blocked, prepare_eligible=false, can_execute=false]
```

- **Nao ha** `main()`, CLI, `systemd`, timer, socket, processo daemon, produtor real para `/run`, credencial ou ferramenta MCP.
- O transporte `httpx` e o diretorio sao **sempre fornecidos pelo chamador de teste**; o codigo de producao nunca instancia `/var/run/docker.sock`, nao escolhe contêiner, URL, metodo, grupo nem local do arquivo.
- O alvo fixo e `HML_TARGET` de `atlas_hml_engine_boundary`; o reader Docker valida nome e labels Compose. O resultado de upstream inadequado (PROD, outra imagem, labels incorretos, erro, status nao-200, resposta muito grande) gera codigo finito e **nao grava uma nova geracao**.
- Uma falha de escrita antes de `os.replace` preserva a geracao anterior; falhas depois do replace exigem checagem externa e nao permitem afirmar rollback completo. Snapshots anteriores podem permanecer legiveis ate expirar pelo TTL; nao assumir revogacao instantanea.
- A rotina retorna apenas `HMLOneShotReceipt`, que tem `status=blocked` e todos os indicadores de autorizacao e atestacao em `false`.

## Evidencias de testes

- `linux-ops-mcp/tests/test_atlas_hml_one_shot_candidate.py`: MockTransport, GET unico, envelope reduzido, leitura de volta, HML estrito, payload com dados privados eliminados, container unhealthy com BLOCKED, upstream recusado, escrita indevida e destino symlink.
- `linux-ops-mcp/tests/test_atlas_hml_one_shot_real_engine_ci.py`: **somente no runner GitHub Actions nao-root com** `GITHUB_ACTIONS=true`, `ATLAS_DISPOSABLE_DOCKER=true` e `ATLAS_REAL_HML_CHAIN_CI=true`. A fixture Docker existente do workflow cria `delpi-hml-public-hub` com labels HML; o teste encaminha atraves do GET guard, salva um arquivo `tmp_path`, usa o leitor por FD e confirma que o estado segue BLOCKED. O runner limpa sua fixture no step `if: always()`.
- `atlas-p22e-integration.yml`: gatilhos e testes atualizados; `linux-ops-mcp-readonly.yml` ja inclui a suite inteira por glob. Cinco verificacoes CI devem ser obtidas no SHA atual da PR.

## Limites materiais: por que ainda nao ativar

1. Um processo que detem acesso real ao Docker Engine possui poder elevado no host, **mesmo que nosso guard Python aceite apenas GET**. O codigo fonte nao o confina, e o GitHub-hosted runner nao atesta o servidor DELPI.
2. A escolha da arquitetura B ainda depende de parecer humano independente: produtor one-shot potencialmente privilegiado + snapshot atomico + atendente UDS sem Docker. Seu gerenciamento por `systemd`, UID/GID, FDs, isolamento de rede, `NoNewPrivileges`, Seccomp, MAC/LSM e perfis ainda nao foi implementado/testado no `srv-api`.
3. Arquivo de snapshot com owner root/mtime recente nao autentica quem o escreveu, nao impede replay por root e nao prova integridade OCI ou revisão realmente implantada.
4. Nao ha `HMLSnapshotInspector` ativado no proxy real; o `serve_one_prebound` continua exigindo `HMLDockerInspectOnly` para pathname real. Esse gate nao deve ser afrouxado antes da revisao de arquitetura.
5. `delpi-verifier` e revisao humana independente nao podem ser substituidos por testes automatizados. Backup/restore, rollback em HML, journal one-shot, aprovacao Core, atestacao OS e checkout continuam pendentes.
6. `PREPARE` e `ACT` seguem desabilitados; nenhum deploy ou alteracao de permissao de contas, servicos, bancos, Keycloak ou Docker pode decorrer do merge.

## Proximo passo que realmente diminui risco

Obter **decisao de arquitetura por revisor Linux/Seguranca** na issue #232 e, somente com aceite, preparar uma PR distinta para o desenho de supervisao isolada com evidencias verificaveis e runbook de rollback. A instalação operacional deve exigir autorizacao administrativa especifica. Caso o parecer seja negativo, descartar B em vez de continuar ampliando codigo candidato sem resolucao da fronteira privilegiada.

## Gates

- [ ] 5 checks GitHub no head final
- [ ] Verificador independente `delpi-verifier` com parecer sem edicao
- [ ] Revisao humana do produtor privilegiado e do isolamento no Docker
- [ ] Nenhum merge automatico, deploy, processo persistente ou novo socket em host
- [ ] Quatro MCP tools READ apenas, PREPARE/ACT OFF
