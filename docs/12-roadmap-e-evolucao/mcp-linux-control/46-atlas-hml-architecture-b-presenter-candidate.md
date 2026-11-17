# ATLAS HML | Arquitetura B escolhida para desenvolvimento e presenter de snapshot não privilegiado

**Data:** 17/11/2026 | **Estado:** DIREÇÃO B APROVADA PELO OWNER / IMPLEMENTAÇÃO SOURCE-ONLY / SEM ATIVAÇÃO  
**Issue de governança:** [#232](https://github.com/roberiooliveiradev/delpi-central/issues/232) | **Roadmap:** etapa 55.

## Decisão, exatamente como autorizada

O owner autorizou seguir a **arquitetura B como direção de desenvolvimento**, após o `delpi-verifier` independente por Cursor `composer-2.5` da PR #245 (`ACCEPT_WITH_RESIDUAL`, nenhuma ordem de correção). Isto **não** autoriza implantar, ativar, abrir socket no host, criar usuário, alterar grupo/ACL, ligar ao MCP, disparar Docker GET no `srv-api`, PREPARE ou ACT. A exigência de parecer humano independente permanece **não atendida**; o próprio owner é o único responsável técnico disponível e essa limitação não pode ser apresentada como independência.

O projeto continuará em branches e PRs separadas, com merge manual, sem anexos de código e sem deploy por merge.

## Modelo de confiança

```text
 Docker Engine do host (poder host-equivalente)
             |
       SOMENTE PRODUTOR EFÊMERO PRIVILEGIADO [NÃO INSTALADO]
             |   - GET do container HML allowlisted (mas Docker raw ainda é risco)
             v
   snapshot JSON atômico (root:atlas-hml 0640) [NÃO INSTALADO]
             |
  LEITOR/PRESENTER sem Docker [NESTA PR, SOMENTE MÓDULO-FONTE]
             |   - verifica FD de arquivo e ACL; exige read-only
             |   - serve UM GET limitado no UDS PREBIND por supervisor
             |   - compara UID do cliente via SO_PEERCRED (Linux)
             v
  cliente ATLAS READ [AINDA NÃO CONECTADO À NOVA FONTE]
             |
       status=blocked; prepare=false; act=false
```

**Ponto essencial:** nem permissões Unix, `NoNewPrivileges`, filtros seccomp nem um GET Python limitado restringem por si só o poder do processo com Docker bruto. O produtor terá que ser autorizado em uma etapa futura, e o presenter precisará demonstrar ausência de Docker bruto tanto por pathname quanto por FD herdado, aliases e rede. O CI da PR #243 provou o risco de FD Docker pré-conectado persistir após trocar UID.

## O que foi implementado neste pacote

Novo `linux_ops_mcp/atlas_hml_snapshot_presenter_candidate.py` com a função interna `_serve_one_prebound_snapshot_review`.

- **Não cria listener:** recebe um socket UNIX previamente aberto em fixture de teste, valida `SO_TYPE=SOCK_STREAM`, `SO_ACCEPTCONN`, endereço, pathname e permissões de socket/diretório pela política já existente.
- **Cliente por identidade de kernel:** `SO_PEERCRED` precisa devolver UID permitido, nunca aceita UID declarado via HTTP. Caminho fixo vincula a identidade `atlas-hml`; caminhos alternativos e leitores injetáveis existem somente para testes descartáveis.
- **Protocolo restrito:** aceita somente GET em `/v1/hml/public-hub/snapshot`, Host exato, sem corpo, autenticação HTTP, query string ou múltiplas solicitações numa mesma leitura. Métodos, paths e headers fora do contrato são recusados antes de qualquer leitura de snapshot.
- **Somente snapshot:** utiliza o leitor FD com `O_NOFOLLOW`, owner/grupo/modos/ACL/mtime validados; não contém cliente Docker, transporte HTTP externo, shell ou import de produtor privilegiado.
- **Resposta reduzida:** apenas `environment=hml`, `service_id=public-hub`, `status=blocked`, sinais `running_untrusted`/`healthy_untrusted`, data declarada não atestada e flags de poder expressamente `false`. Não inclui credenciais, env/mounts, caminhos, IDs Docker, claims de assinatura ou comandos.
- **Falha fechada:** snapshot indisponível, adulterado, sem ACL verificável ou diagnostic fraudulento produz recusa 503 sanitizada. Mesmo GET 200 **não é autorização operacional** nem atestado de origem; o resultado de controle permanece sempre `blocked`.
- **Zero integração operacional:** sem `__main__`, `main()`, `server.py`, nova tool MCP, unit systemd, socket ativável, compose, Keycloak, DB, scheduler, deploy, host mount ou mudança no `srv-api`.

### Testes negativos e controle

Arquivo `linux-ops-mcp/tests/test_atlas_hml_snapshot_presenter_candidate.py`, incluído nos gates Linux MCP e Docker descartável.

- UDS AF_UNIX verdadeiro em `pytest tmp_path` com `SO_PEERCRED` do kernel, request válida, bloqueio contínuo, dados allowlisted e resposta no-store.
- Mesmo com `running=True` e `healthy=True`, não é permitida promoção para PREPARE/ACT.
- Métodos POST/DELETE/HEAD, PROD, paths Docker, query, Host falso, falta de Host, pipelining, corpo, tokens HTTP e request oversized rejeitados antes de ler arquivo.
- UID diferente do peer negado com 403; owner inadequado e socket não confiável recusados.
- Snapshot inexistente, PROD falsificado, expirado, symlink, ACL não verificável e `SnapshotDiagnostic` com `prepare_eligible=True` negados sem refletir valores sensíveis.

## O que este CI prova e o que não prova

**Prova apenas no runner descartável:** parser, peer UID kernel, limites do socket de teste, leitor FD, recusa de requests adversariais e diagnóstico `BLOCKED`. Não prova ownership root real, não inicia serviço, não verifica root produtor, inode `/run` do host ou FDs herdados do processo `systemd`.

**Fora de escopo nesta etapa:** produtor efetivo, `systemd` operacional, gestão de segredos, autenticidade criptográfica do snapshot, anti-replay de root, rollback pós-rename e ligação do MCP ao presenter. Esses tópicos devem ser objeto de uma PR própria e revisão independente antes de qualquer ativação.

## Gatilhos que continuam exigindo ação humana

| Gate | Necessário para | Situação |
|---|---|---|
| Decisão arquitetura B como rumo de projeto | Continuar desenvolvimento source-only | **CONFIRMADO PELO OWNER** |
| Revisão independente de código desta PR (Cursor/DELPI Verifier) | Encerrar entrega de código | **PENDENTE** |
| SEC-01: revisor humano independente de Segurança ou exceção formal explícita | Avaliar risco operacional | **PENDENTE** |
| SEC-02..SEC-05: isolamento do produtor/presenter/UDS real | Instalação em HML | **PENDENTE** |
| SEC-06..SEC-07: testes host de replay, falha, emergência e rollback | Ativação piloto | **PENDENTE** |
| SEC-08..SEC-10: verificação, change-control, Core, PREPARE/ACT segregados | Avanços futuros | **PENDENTE / BLOQUEADO** |

## Próximo passo

Após merge e `delpi-verifier` da presente PR, preparar uma **etapa separada** para blueprint operacional de **homologação somente**, incluindo inspeção dos FDs transmitidos por systemd, autoridade root do produtor, alternativas de segregação, plano de rollback e justificativa/aceite explícitos de qualquer exceção de segregação de funções.

**Sem autorização operacional nova, não executar comandos de `git pull` ou deploy do ATLAS no `srv-api` para ativar esta funcionalidade. Progresso global estimado permanece 52% até evidência de host.**
