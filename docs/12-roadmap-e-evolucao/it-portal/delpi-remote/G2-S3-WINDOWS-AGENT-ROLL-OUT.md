# G2-S3 | Pacote assistido Windows: agendamento e desinstalacao

**Estado em 13/11/2026:** EM REVISAO. Codigo preparado; SEM assinatura corporativa, instalacao ou teste em Windows real. O operador nao esta no escritorio e retomara o piloto presencial depois.

## Escopo da entrega

- Install-ItPortalWorkstationAgent.ps1: default apenas PLANO, sem alteracoes. Com -Activate exige Windows PowerShell 5.1, hostname correto, pacote Authenticode assinado por certificado aprovado, UUID da workstation, cliente Keycloak S2S exclusivo e primeiro envio confirmado. Cria pasta LOCALAPPDATA por UUID, credencial protegida com DPAPI CurrentUser, ACL restrita e tarefa de inventario **DESABILITADA**.
- Invoke-ItPortalWorkstationScheduledSnapshot.ps1: consulta configuracao local, checa hostname e assinaturas do pacote, executa somente coletor G2-S1 + emissor G2-S2, registra log CSV minimo com rotacao, sem dados do inventario, token ou texto HTTP.
- Enable-ItPortalWorkstationAgent.ps1: PLANO por padrao; com -Activate confere usuario/agendamento, verifica assinaturas e faz novo envio S2S antes de habilitar.
- Uninstall-ItPortalWorkstationAgent.ps1: PLANO por padrao; exige -Activate -RevokedInKeycloak -BindingRemoved e confere UUID, usuario e tarefa para desabilitar/remover somente o pacote do dispositivo.
- Test-ItPortalWorkstationAgentPlan.ps1 e tests/test_workstation_agent_package.py: guardas contra efeitos colaterais, credenciais embutidas e ativacao acidental.
- CI de it-portal-api: parser PowerShell do pacote, execucao do modo PLANO em pwsh e pytest.
- NENHUMA migration, API, manifesto, Compose, acesso remoto, instalacao de servico ou usuario foi modificada por G2-S3.

## Gates operacionais

1. Testar coleta LOCAL G2-S1 em Windows corporativo autorizado, com o operador presente. Confirmar JSON sem dados sensiveis publicados.
2. Habilitar G2-S2 somente em piloto aprovado, com um cliente confidencial Keycloak exclusivo por workstation, audiencia correta, scope it-portal.workstations.ingest, TLS, mapeamento client_id -> UUID 1:1 no env PRIVADO e revogacao comprovada.
3. Assinar scripts de release com certificado corporativo e validar assinatura Authenticode Status=Valid e thumbprint aprovado. O codigo-fonte do GitHub nao esta assinado: **NAO executar -Activate com checkout cru**. Registrar checksums e assinaturas sem copiar chave privada ao repo publico.
4. O agendamento usa -LogonType Interactive e -RunLevel Limited. **Funciona somente enquanto a conta Windows que cifrou o segredo estiver logada.** Nao salva senha Windows e nao e um servico persistente/unattended. Funcionar antes do login ou apos logout exige arquitetura futura (conta de servico/gMSA, protecao de segredo apropriada e novo gate).
5. Instalacao, habilitacao e remocao sao operacoes SEPARADAS e exigem -Activate explicitamente. A instalacao cria a tarefa DESABILITADA e nunca substitui tarefas/pacotes existentes.
6. Segredo Keycloak fica em DPAPI do usuario local; nunca publicar token, serial, IP, hostname ou payload de equipamento real no GitHub.
7. Nenhum privilegio de acesso remoto, controle de tela, shell ou arquivos pode derivar deste agente. Gate G0-SEC permanece pendente.

## Modo PLAN (seguro, somente apos pacote revisado)

    $plan = @{
      ApiBaseUrl = 'https://minhadelpi.com.br/apps/it-portal-api'
      S2sTokenUrl = 'https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/token'
      ClientId = '<client-individual-autorizado>'
      WorkstationId = [guid]'<uuid-do-ativo-no-portal>'
      ExpectedHostname = '<hostname-do-windows-piloto>'
      IntervalMinutes = 60
    }
    .\Install-ItPortalWorkstationAgent.ps1 @plan

Sem -Activate, o comando apenas imprime o plano. Com piloto autorizado, scripts assinados e primeiro envio S2S liberado, executar PRESENCIALMENTE:

    $plan.TrustedSignerThumbprint = '<thumbprint-certificado-aprovado-40-hex>'
    .\Install-ItPortalWorkstationAgent.ps1 @plan -Activate

A instalacao cria tarefa DESABILITADA, nao habilita coleta. A habilitacao, depois de novo smoke, e separada:

    .\Enable-ItPortalWorkstationAgent.ps1 -WorkstationId $plan.WorkstationId -Activate

A desinstalacao requer primeiro revogar no Keycloak e retirar o binding privado; depois:

    .\Uninstall-ItPortalWorkstationAgent.ps1 -WorkstationId $plan.WorkstationId -RevokedInKeycloak -BindingRemoved -Activate

**Estes tres comandos -Activate sao exemplos futuros, nao executar remotamente agora.** No Windows, inspecionar -Confirm e os resultados; parar em qualquer falha de assinatura, hostname, S2S ou ACL.

## Gates de validacao

- [ ] Sintaxe PowerShell e plano default sem efeitos no CI
- [ ] Testes Python de seguranca e regressao da API aprovados
- [ ] Assinatura corporativa e checksums de release registrados
- [ ] G2-S1 Windows 11 PowerShell 5.1 real validado
- [ ] Keycloak S2S individual/revogacao e binding 1:1 testados em um ativo
- [ ] Instalacao confirma primeiro snapshot e cria tarefa Disabled
- [ ] Enable, periodicidade, logs, falha de rede e comportamento apos logout testados
- [ ] Revogacao Keycloak, remocao binding e desinstalacao local verificadas

## Rollback e continuidade

Como G2-S3 so cria arquivos de script/CI/docs no repo, **nao ha deploy de API/frontend nem migration neste incremento**. Se o piloto nao foi ativado, rollback = nao distribuir pacote. Se ativado, revogar Keycloak e binding, depois desabilitar/remover tarefa e pasta exclusiva do UUID. Nao usar script para alterar outros servicos Windows/TOTVS.

**Proximo passo presencial:** G2-S1 coleta local -> G2-S2 envio manual com token exclusivo -> assinatura de release -> G2-S3 instalacao desabilitada -> teste/Enable/Uninstall. Registrar provas e aceite na issue #179. Acesso remoto somente apos G0-SEC.
