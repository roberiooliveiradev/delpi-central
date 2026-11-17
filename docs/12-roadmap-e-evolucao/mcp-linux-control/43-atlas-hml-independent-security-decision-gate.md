# ATLAS HML | Gate de decisão da arquitetura e revisão independente (#232)

**Data:** 17/11/2026 (BRT)  
**Estado atualizado (17/11/2026):** arquitetura B escolhida para DESENVOLVIMENTO; decisão OPERACIONAL e SEC-01..10 continuam PENDENTES / SOURCE-ONLY  
**Escopo:** apenas `delpi-hml-public-hub` no Compose `delpi-hml`, serviço `public-hub`  
**Referências:** [issue #232](https://github.com/roberiooliveiradev/delpi-central/issues/232), [PR #240](https://github.com/roberiooliveiradev/delpi-central/pull/240), [runbook 38](./38-atlas-hml-supervisor-architecture-proposal.md), [runbook 42](./42-atlas-hml-supervisor-blueprint-review.md)

> Este dossiê é um **pedido de decisão de segurança** e uma matriz de evidências. Não é aprovação, atestado, protocolo instalável, execução de `delpi-verifier`, ordem de serviço, permissão de deploy ou de PREPARE/ACT. **Nenhuma instalação, operação Docker, mudança no host, Keycloak ou banco está autorizada por este documento.**

> **Atualização de governança (17/11/2026):** o owner aprovou a opção **B somente como direção de desenvolvimento** na [issue #232](https://github.com/roberiooliveiradev/delpi-central/issues/232#issuecomment-6956046761). As PRs #251 e #253 foram integradas após revisão de código por modelo independente; isso não substitui parecer **humano** de Segurança nem altera o risco host-equivalente do produtor com Docker bruto. Este documento conserva a análise histórica A/B/C, mas a decisão que falta é exclusivamente **autorizar ou rejeitar uma operação HML futura**, após SEC-01..10 e rollback. Consultar o [runbook 48](./48-atlas-hml-b-preativacao-evidencias-rollback.md) para os controles e para a diferença entre um índice de evidências não confiáveis e atestação real. Não instalar nem converter blueprints `.review`.

## 1. Decisão que precisa ser tomada agora

Após as PRs #234, #236, #237, #239 e #240, existem parser HML estrito, leitor de snapshot via FD, publicador atômico, montagem one-shot testada com Docker descartável e cinco blueprints `.review` deliberadamente não instaláveis. Os checks em CI **não comprovam isolamento no `srv-api`**.

Há três alternativas. A avaliação abaixo é uma **recomendação de engenharia, não a decisão do owner nem parecer de Segurança**:

| Alternativa | Limite de privilégio | Proposta de encaminhamento | Condição impeditiva |
|---|---|---|---|
| **A**: proxy Python permanente com Docker bruto | Processo persistente com poder equivalente a root; regras GET no Python podem ser contornadas por processo comprometido | **Não escolher para o piloto sem barreira externa comprovada** | Revisão independente precisa justificar como o acesso bruto ao Engine seria efetivamente restringido |
| **B**: produtor one-shot root + arquivo de snapshot + apresentador sem Docker | Reduz a janela do processo privilegiado e remove a API bruta do processo persistente; produtor ainda tem poder de host | **Candidata preferida, condicional** | Aprovação humana de risco residual, isolamento real e testes no host, sem autorizar o produtor nesta etapa |
| **C**: plugin de autorização no próprio Docker Engine | Política aplicada junto ao Engine | **Adiar para change-control próprio** | Altera o daemon compartilhado, com possível impacto em produção |

**Questão a decidir:** a Segurança e o owner aceitam a alternativa B com produtor root de vida curta, cientes de que um compromisso do produtor enquanto detém o Engine continua host-equivalente? Se a resposta for não, a implementação operacional B deve ficar suspensa, com reavaliação de C ou outra fronteira de confiança. A escolha não pode ser inferida de merge, CI, texto de blueprint ou resposta do próprio ATLAS.

## 2. Fronteiras de confiança a avaliar

```text
                         LIMITE DE PRIVILÉGIO ELEVADO
[Docker Engine compartilhado] <--socket/FD--> [produtor root one-shot]
                                                  |
                                       JSON HML reduzido + atomic rename
                                                  |
                                               [snapshot]
                                                  |
                     SEM DOCKER / SEM FD BRUTO / SEM REDE ALTERNATIVA
                                                  |
                           [apresentador dedicado atlas-hml]
                                                  |
                              [UDS HML autenticado por peer]
                                                  |
                               [coletor ATLAS READ ONLY]

Independente da alternativa: status BLOCKED / PREPARE OFF / ACT OFF.
```

1. **Produtor:** comprometimento antes, durante ou após acesso ao socket Docker; possibilidade de comandar o Engine fora do cliente GET; integridade e origem do binário/configuração; dependências, variáveis, file descriptors, credenciais e herança; duração real do poder elevado e impacto em contêineres de terceiros.
2. **Snapshot:** conteúdo mínimo HML, propriedades POSIX e troca atômica são controles necessários, mas **não autenticam o produtor perante root comprometido**. Avaliar rollback, repetição, troca de geração, relógio, TTL, falha entre rename e fsync e recusa de documento de PROD.
3. **Apresentador:** restrições `InaccessiblePaths`, `RestrictAddressFamilies`, UID e grupos não provam ausência de aliases, Docker TCP, ACLs, namespaces ou FDs herdados. `NoNewPrivileges` e seccomp são defesa em profundidade, não autorização.
4. **Socket e pai:** `SocketGroup=atlas-hml` não define ownership do diretório. Pai `root:atlas-hml` modo 0750, UDS `root:atlas-hml` 0660; conferir permissões efetivas, ACL, symlinks, mounts, namespace, peer real e socket activation.
5. **Superfície de operação:** nenhum elemento pode acessar, reiniciar, recriar ou inspecionar indiscriminadamente `delpi-public-hub` de produção. A prova de revisão Git HEAD não comprova imagem/implantação.

## 3. Matriz de evidências exigidas antes de autorizar qualquer instalação

Em cada linha, **ausência de evidência, dúvida, evidência não reproduzível ou contradição mantém o gate BLOQUEADO**. O revisor deve registrar artefato, origem, data, escopo e hash quando aplicável, distinguindo fonte de CI descartável de observação de host.

| ID | Evidência requerida | Responsável proposto | Exemplo de falha que deve ser recusada |
|---|---|---|---|
| **SEC-01** | Parecer independente identificável sobre A/B/C, justificativa e risco residual do processo com Docker bruto | Linux/Segurança independente | Proclamar B aprovada porque CI verde ou porque blueprint contém `NoNewPrivileges=yes` |
| **SEC-02** | Origem e integridade revisadas do futuro artefato do produtor, identidade real, cadeia de execução, escopo da API Docker, tempo de privilégio e FD heredável | Linux/Segurança | Produtor consegue abrir Engine por alias não modelado; código GET tomado como fronteira |
| **SEC-03** | Prova no host do apresentador efetivo sem acesso Docker por path, ACL, grupo, FD herdado, rede ou socket alternativo; incluir ensaio de tentativa negada | Linux/Segurança | Verificação baseada apenas em duas paths conhecidas ou lista de grupos |
| **SEC-04** | Identidade, capability sets, `NoNewPrivileges`, seccomp, namespaces, LSM/MAC e política systemd da **unidade real**, não da sessão manual | Linux/Segurança | Copiar valores do processo `sudo -u atlas-hml` como evidência da unidade |
| **SEC-05** | Caminho do UDS e de todos os pais: owner/grupo/modos efetivos, ACLs, symlink/TOCTOU, FD recebido via socket activation e `SO_PEERCRED` | Linux/Segurança | Assumir que `SocketGroup` prova o grupo do pai |
| **SEC-06** | Testes HML negativos para alvo PROD, imagem errada, snapshot ausente/stale/adulterado/replay, falha do produtor e atomicidade/rollback; zero PREPARE/ACT | Infra + Segurança | Documento stale considerado autêntico ou falha com promoção de permissões |
| **SEC-07** | Ensaio autorizado de parada, recuperação e retirada apenas dos novos componentes, preservando Docker daemon e Public Hub PROD | Infra / owner HML | Plano exige reiniciar o Docker ou apagar recursos compartilhados |
| **SEC-08** | Evidência `delpi-verifier` por outro agente/modelo, sem edição do veredito e com ordens de correção encerradas ou decisão formal | Revisor independente | Autoverificação pelo executor ou apenas GitHub Actions |
| **SEC-09** | Autorização operacional específica com janela, responsáveis, plano de observação, inventário de mudanças e rollback | Owner HML + Segurança | Tratar merge, esta matriz ou issue como autorização de deploy |
| **SEC-10** | Revalidação de quatro ferramentas MCP exclusivamente READ; gates Core, journal one-shot, S2S, backup/restore e PREPARE/ACT continuam segregados | Owner do control-plane | Confundir piloto READ de HML com liberação de PREPARE/ACT |

**Evidência de código já disponível:** testes e contratos de `linux-ops-mcp/tests/test_atlas_hml_one_shot_real_engine_ci.py`, `test_atlas_hml_supervisor_blueprint_review.py` e módulos em `linux_ops_mcp/atlas_hml_*`. São ponto de partida para revisão, não substituem SEC-02 a SEC-09.

## 4. Protocolo de decisão e assinaturas

A issue #232 é o lugar canônico da decisão. Segurança deve anexar parecer **independente** com respostas SEC-01 a SEC-10 e resultado explícito em cada item: `COMPROVADO`, `REPROVADO` ou `PENDENTE`, com evidência ou justificativa. Autodeclarações do candidato e screenshots isolados não equivalem a prova.

Preencher no parecer externo, **não neste arquivo versionado como autoaprovação**:

| Campo exigido | Preenchimento pelo responsável |
|---|---|
| Identidade / área do revisor e independência da implementação | PENDENTE |
| Data, ambiente e versões exatas dos objetos revisados | PENDENTE |
| Alternativa escolhida (A, B, C ou nenhuma) e fundamento | PENDENTE |
| Riscos residuais aceitos/rejeitados, especialmente Docker host-equivalente | PENDENTE |
| Evidências SEC-01..SEC-10, negativas e limites | PENDENTE |
| Parecer do `delpi-verifier` e ordens de correção | PENDENTE |
| Decisão nominativa do owner e escopo da autorização operacional futura | PENDENTE |

**Regra de falha:** enquanto a decisão e evidências forem pendentes, a arquitetura permanece `DECISION_REQUIRED`. Mesmo um parecer favorável a B **não autoriza automaticamente um serviço root**, não instala nada e não promove `prepare_eligible` ou `can_execute`. Uma futura operação HML requer mudança separada, revisão do código executável e autorização explícita.

## 5. Sequência de trabalho que realmente remove o bloqueio

1. Entregar este pedido de decisão para Linux/Segurança, com PR #240 e runbooks 38 a 42, **sem habilitar blueprints ou criar binários de produção**.
2. Revisor independente avaliar SEC-01..SEC-05 sobre a fronteira de privilégio; se a alternativa B for reprovada, interromper o trabalho de presenter/produtor operacional e rever arquitetura.
3. Owner registrar **decisão humana** na issue #232. Corrigir lacunas da análise, se houver, no próprio dossiê, em uma PR coerente e revisada.
4. **Só depois** planejar e implementar presenter sem Docker, produtor one-shot e supervisão em PR de código própria, com `delpi-verifier`, testes negativos descartáveis e change-control HML.
5. Com autorização operacional **separada**, executar ensaios SEC-03..SEC-07 no `srv-api` sobre o piloto HML, usando runbook de rollback aprovado. Produção permanece intocada.
6. Continuar com control-plane PREPARE/ACT somente após seus gates específicos, independentes da observação HML.

## 6. Limites desta entrega

- Nenhum comando operacional, instalador, `systemctl`, `tmpfiles`, socket ou Docker é executado.
- Nenhum código runtime, API, imagem, migração, IAM, token, banco, host ou grupo é alterado.
- A PR de documentação **não mede isolamento no host**, não é `delpi-verifier` nem substitui revisão humana.
- A estimativa do ATLAS até primeira implantação governada em PROD **permanece 52%**; este dossiê organiza a decisão, mas não resolve a evidência operacional.

**Resultado esperado:** o owner e a Segurança dispõem de uma decisão claramente formulada e uma lista verificável de provas exigidas. O próximo avanço não é outro protótipo: é **parecer independente na issue #232**.
