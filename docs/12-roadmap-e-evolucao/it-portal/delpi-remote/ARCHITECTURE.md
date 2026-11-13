# Delpi Remote | Arquitetura proposta e ADR-001

**Data:** 2026-11-13 | **Estado:** proposta de engenharia documentada, ainda sem homologacao de seguranca.

## Situacao verificada

- `plugins/it-portal`: React 19/TypeScript, menu e componentes compartilhados.
- `it-portal-api`: FastAPI, banco PostgreSQL no schema `it_portal`, migrations versionadas e RBAC do Core.
- Coletores Windows vigentes: metricas/observacoes, servicos SCM e **controle restrito de iniciar/parar/reiniciar servicos explicitamente aprovados**.
- Nao foi identificada uma implementacao vigente de inventario de desktops ou de controle grafico remoto no Portal de TI.
- Repositorio publicado de forma publica; segredos, logs de hosts e topologia real **nao** pertencem ao codigo.

## Decisao ADR-001: Portal proprio + motor de acesso remoto open source isolado

**Escolha inicial para provar em laboratorio:** MeshCentral self-hosted como motor de tela/teclado/mouse/clipboard/arquivos, com integracao ao Portal de TI. **Nao presumir** que OIDC e sessao incorporada atendam aos requisitos sem prova de isolamento e revogacao. Uma integracao indireta com API/broker pode ser necessaria.

**Por que nao criar um protocolo remoto proprio no MVP?** Captura de tela, escritorio seguro do Windows, encoding, transferencia, autenticacao do agente, multiplos monitores, reconexao e manutencao de criptografia elevam risco e custo. A interface, RBAC, auditoria, fluxos e inventario continuam sob responsabilidade DELPI.

**Opcao de saida:** caso licenca, seguranca ou embed nao sejam aceitaveis, comparar plataforma open source alternativa ou motor dedicado. Registrar ADR de substituicao antes de implementar.

**Referencias oficiais:**
- https://docs.meshcentral.com/ (visao geral/licenca Apache-2.0)
- https://docs.meshcentral.com/meshcentral/ (guia, rede e backup)
- https://docs.meshcentral.com/meshcentral/security/
- https://docs.meshcentral.com/meshcentral/agents/
- https://docs.meshcentral.com/meshcentral/agent-downloads/ (downloads/artefatos exatos)

## Fronteiras

```text
[Navegador humano Portal de TI]
         | Keycloak e Core RBAC + MFA
         v
[Plugin it-portal] ---> [it-portal-api: inventario + politica + auditoria]
                               |
                [broker de sessao: isolado, desabilitado]
                               | token curto, destino vinculado e revogavel
                               v
                 [MeshCentral self-hosted isolado]
                               ^
                               | conexao TLS de saida do agente
                               |
                 [Estacao Windows gerenciada]
```

A **identidade do dispositivo** deve ser diferente da identidade do usuario. Inventario e controle remoto sao duas capacidades separadas. A identidade do agente de inventario **nao** deve autorizar sessao remota.

### Inventario de estacoes (owner: it-portal-api)
- Nova entidade `workstations`, referencia estavel UUID distinta da identidade de rede.
- Dados curados: nome, hostname, unidade, tipo de dispositivo, setor/local, estado administrativo, observacoes e responsavel corporativo quando necessario.
- Dados observados em estrutura separada: hardware, RAM/CPU/discos, sistema, IP/MAC e ultimo contato, cada qual com `source` e `observed_at`; nao sobrescrever o cadastro curado.
- IP, MAC e hostname **nao** sao credenciais, nem chave primaria, nem garantia de identidade. Evitar duplicidade por reconciliacao controlada; registrar divergencias.
- `workstations` nao deve compartilhar tabela/rotas de `servers` para nao misturar criticidade, vinculos de banco e controles de servico de servidor.
- Nao coletar documentos pessoais, conteudo de arquivos, historico de navegacao nem conteudo de clipboard.

### Agentes
- Inventario G2: somente leitura, envio HTTPS, credencial individual protegida localmente, rate-limit e escopo de ingestao exclusivo.
- Remoto G3-G5: agente/capacidade independente, distribuido somente em equipamento corporativo autorizado. Validar assinatura/checksum e versoes; revogacao e desinstalacao gerenciadas.
- Nunca reaproveitar secrets de outros servidores/estacoes, nem abrir inbound RDP/WinRM nas estacoes como atalho.
- Status do painel distingira online, offline e desatualizado.

### Sessao de controle (a construir somente depois de G0-SEC)
1. Usuario abre o portal autenticado; MFA recente para operacao privilegiada.
2. API valida `it-portal.remote.connect` com RBAC fresco + allowlist **por operador e equipamento** (superadmin geral nao basta por si so).
3. API valida politica especifica para modo nao assistido, janela, vinculo com chamado/motivo e risco do equipamento.
4. Broker emite capacidade de **uso unico**, expirada em curto periodo e vinculada a operador+destino+escopo, sem senha mestre, e inicia a sessao autorizada.
5. Usuario e operador recebem indicacao clara da sessao; logar inicio/fim/resultado e permitir encerramento por ambos conforme politica.
6. Revogacao RBAC, logout, perda de MFA, encerramento forcado e kill switch impedem novas sessoes e devem interromper as ativas no prazo testado.
7. Clipboard e arquivo exigem permissao e habilitacao **separadas**; nao enviar conteudo bruto para logs.

### Acesso administrativo
Controle grafico nao equivale a privilegio administrativo do Windows. Contas e elevacao locais devem respeitar Windows/UAC, politicas de dominio e trilha de auditoria. Nao implementar bypass de UAC, credential dumping, senha mestre ou shell arbitrario pela API do inventario. Funcionalidades elevadas so apos desenho e aceite proprios.

### Rede e operacao
- MeshCentral em VM/servico isolado, com backup e restauracao demonstrados, versao fixada e atualizacoes monitoradas.
- Acesso preferencial pela rede privada/VPN entre SC e ES; nao expor a Internet por padrao.
- TLS validado ponta a ponta, certificados e segredos em cofre, limites de acesso, CSP/iframe e proxy seguros.
- Fazer threat model para sessao incorporada: cookie, CSRF, clickjacking, tokens, cross-origin e WebSockets. Sem colocar token tecnico do motor no navegador.
- Kill switch **independente** do controle de servicos Windows existente.
- Escalar por ondas, primeiro 1 computador de laboratorio, nunca servidores TOTVS/producao como piloto.

## ADR pendentes para pesquisa/aceite
- ADR-002: versao exata/licenca/SBOM do MeshCentral, suporte a clipboard e UAC no Windows usado, mantenedores e ciclo de atualizacao.
- ADR-003: compatibilidade e modelo de embed/SSO seguro sem sessao paralela; integracao API/broker.
- ADR-004: endpoints de rede, VPN, recursos de servidor, segregacao e backups com equipe de infraestrutura.
- ADR-005: politica de transparencia, privacidade, acesso nao assistido e retencao de auditoria.
