# G0-SEC-S2 | Minuta de isolamento de rede e acesso ao motor remoto

**Status:** MINUTA para TI e Infra/Seguranca. **Gate:** G0-SEC. **Nenhum host/porta foi liberado.**
**Escopo:** arquitetura futura **somente laboratorio**; o projeto ainda nao possui servidor MeshCentral, broker ou endpoint remoto instalado.

## 1. Fronteiras de confianca

```text
[Operador autorizado + MFA]
          |
  navegador -> Portal do TI + Core
          | autorizacao fresh, allowlist, finalidade, ticket
          v
   [Broker remoto isolado]          (FUTURO, NAO IMPLEMENTADO)
          | credencial efemera, destino explicito e TTL
          v
   [Motor remoto em segmento LAB]   (NAO INSTALADO)
          |
      estacao LAB aprovada          (NENHUM AGENTE INSTALADO)
```

Sem caminho direto do navegador ao administrador do motor. Credenciais privilegiadas nao chegam ao frontend. A identidade tecnica do coletor G2-S2 **nao** e identidade de controle remoto. Uma eventual integracao com Keycloak precisa de revalidacao por sessao e negacao se Core/Keycloak nao estiverem disponiveis.

## 2. Matriz de fluxos PROPOSTA, nao regras de firewall

| Origem | Destino | Finalidade | Gate |
|---|---|---|---|
| Navegador na rede privada/VPN | Portal + Core | Login humano, MFA e solicitacao | Sem superficie remota ate G0-SEC |
| Portal API | Broker no laboratorio | Autorizar sessao efemera apos RBAC fresh | **DENY** no momento |
| Broker | Motor no segmento LAB | Criar/encerrar sessao com token curto | **DENY** no momento |
| Motor LAB | Computador LAB | Fluxos remotos estritamente necessarios | **DENY** no momento |
| Motor/Broker LAB | Producao TOTVS, AD, SQL, MyWEG | Nenhum | **DENY** permanente por padrao |
| Internet publica | Motor/Broker/estacao LAB | Nenhum | **DENY** |
| Estacao sem enrolment | Motor remoto | Nenhum | **DENY** |
| Motor LAB | atualizacoes/artefatos externos | Somente via fonte controlada, se aprovada | **DENY** ate supply chain verificada |

**Nao definir IPs, FQDN internos, VLANs, subnet ou portas reais neste documento publico.** Infra devera produzir em repositório privado uma matriz de conexoes, regras, DNS, proxy, certificado, firewall e caminhos de egress testados com as portas estritamente necessarias para o artefato escolhido.

## 3. Controles exigidos antes do laboratorio

1. **Deny-by-default** em entrada e saida, segmentacao LAB separada da producao, regras explicitas por origem/destino/porta e ausencia de NAT/publicacao externa.
2. **TLS** do navegador ao Portal e nas fronteiras internas relevantes; certificado confiavel, rotacao e validacao, sem `verify=false`.
3. **Keycloak e Core:** MFA recente, RBAC por operador/maquina, escopos separados de inventario e de servidores e resposta fail-closed em falha de SSO.
4. **Broker:** tokens de uso unico, vinculados ao operador, dispositivo, origem e finalidade, TTL curto; rejeicao de replay e mudanca de destino, revogacao ativa, audit trail.
5. **Motor:** acesso administrativo via acesso privilegiado limitado, sem console publico, sem conta mestra em app de navegador, sem autoenrolment de producao.
6. **Agente:** apenas VM de laboratorio sem documentos reais e sem acesso aos recursos criticos; imagem conhecida, hashes e rollback verificados.
7. **Monitoramento:** tentar acessar o motor de origem nao autorizada deve falhar; bloquear usuario sem MFA/role, estacao sem allowlist e sessao expirada deve falhar.
8. **Kill switch:** caminho independente para impedir novas sessoes e terminar as ativas, comprovado em teste de laboratorio.

## 4. Evidencias a coletar em ambiente privado

- Diagrama efetivo com redes e regras, validado por Infra/Seguranca.
- Resultado de teste de isolamento a partir de rede nao autorizada e da LAN produtiva: nenhuma sessao ou console administrativo acessivel.
- Lista de fluxos necessarios com justificativa e registro de change, sem regra ampla `0.0.0.0/0` de entrada.
- Captura de handshake TLS/certificados e testes negativos de revogacao e MFA.
- Plano de quebra de conectividade e registro de impacto em outras aplicacoes.

## 5. Condicoes de NO-GO

Exposicao publica, ponteamento para servidores TOTVS, credential sharing, ausencia de encerramento remoto, rotas de rede nao auditadas, falta de TLS, impossibilidade de revogar o motor ou artefato MeshCentral sem mitigacao da vulnerabilidade reportada resultam em **NO-GO**.

**Este desenho nao configura firewall, DNS, VPN, proxy, containers, certificados ou software remoto.** O desenho definitivo depende de aprovacao privada e testes, e o gate G0-SEC permanece pendente.
