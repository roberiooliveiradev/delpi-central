# G0-SEC-S2 | Minuta de revogacao, incidente e recuperacao

**Status:** MINUTA para TI/Infra/Seguranca. **Gate:** G0-SEC. **Nenhum kill switch remoto foi implementado.**
**Ambiente:** laboratorio isolado futuro; nenhuma acao deste documento deve ser aplicada a servidores de producao.

## 1. Modelo de revogacao proposto (a implementar e testar)

**Nivel 1: operador**. Ao revogar RBAC, remover role, desligar MFA ou bloquear conta, negar imediatamente novas sessoes e encerrar as existentes em prazo **a definir e medir no piloto**. O navegador nao conserva token privilegiado nem ignora revogacao no backend.

**Nivel 2: dispositivo**. Retirar computador da allowlist e revogar identidade/agent remoto **independente** do cliente de inventario G2. Nao confiar apenas em endereco IP ou hostname como autenticador.

**Nivel 3: global**. Desabilitar novas sessoes no broker e encerrar sessoes ativas; operacao precisa de caminho independente do SSO/Portal em caso de indisponibilidade. Se a revogacao logica falhar, Infra deve poder isolar a rede LAB. O mecanismo real exige desenho, implementacao e teste antes de GO.

**Garantia de seguranca:** se Keycloak/Core/broker estiverem indisponiveis, o sistema deve negar nova sessao e nao permitir credencial alternativa fixa; nao prometer encerramento em tempo exato sem teste.

## 2. Playbook de incidente, ordem para exercicio controlado

1. **Detectar e classificar:** conta comprometida, sessao indevida, alertas de vulnerabilidade do motor ou movimentacao inesperada. Registrar incidente em canal **privado**, sem publicar dados pessoais.
2. **Conter:** bloquear novos acessos e sessoes pelo kill switch do laboratorio, revogar tokens e clientes envolvidos e isolar LAB da rede produtiva se necessario. Nunca usar bloqueio genérico de infra critica sem janela/autorizacao.
3. **Preservar evidencia:** eventos de autenticacao, autorizacao, tentativas e sessions com timestamps; proteger integridade/cadeia de custodia; evitar copiar conteudo da tela ou arquivos.
4. **Avaliar abrangencia:** quais identidades, endpoints LAB e credenciais foram expostos; determinar se producao pode ter sido afetada. Escalar a Seguranca/TI e, se aplicavel, Juridico/RH e areas de resposta a incidente.
5. **Erradicar e recuperar:** refazer instancia de laboratorio a partir de imagem confiavel, corrigir falha, rotacionar tokens e certificados, validar configuracao e isolamento antes de reabrir.
6. **Verificar e aprender:** reproduzir em ambiente controlado negacao de novas sessoes, encerramento de ativas e trilhas de auditoria; registrar acao preventiva e aprovacao da retomada.

**NUNCA** usar uma instalacao ainda nao homologada para acessar remotamente maquina de colaborador, mesmo durante incidente.

## 3. Backup e recuperacao, requisito para G3

- **Inventariar:** banco/config/segredos e certificados do motor de laboratorio, firmware/agent de teste, variaveis de runtime e historico de sessao (metadados minimos). Nao colocar credenciais, topologia real ou backups no GitHub.
- **Segredos:** armazenar em cofre de producao/seguranca apropriado ao laboratorio; backup criptografado e com acesso restrito. Nao salvar tokens no frontend.
- **Frequencia e retencao de backup:** **A DEFINIR por TI/Infra**, vinculadas ao RPO, RTO, obrigacoes de privacidade e capacidade de restaurar.
- **RPO e RTO:** **PENDENTES**; devem ser acordados antes do piloto. Nao afirmar SLA ou seguranca de restauracao apenas porque um `pg_dump` foi concluido.
- **Teste de restauracao:** usar uma VM LAB descartavel sem rede produtiva, restaurar config e dados necessarios, validar certificado/identidade/segregacao, registrar sucesso/falha e tempo medido.
- **Plano de rollback:** ao falhar a release ou teste de revogacao, fechar o acesso no broker, retirar o laboratorio da rede, revogar clientes, restaurar imagem/versao aprovada e documentar retorno. **Nao** apagar migration/prod data para desfazer motor remoto.

## 4. Exercicios de mesa sem execucao tecnica

| Cenario | Resultado a demonstrar em futuro LAB | Evidencia privada |
|---|---|---|
| Operador perde role durante sessao | Nenhuma nova sessao, ativa encerrada no tempo medido | Eventos authz/kill |
| Token de sessao copiado ou reutilizado | Replay e destino diverso negados | Eventos sem token em claro |
| Falha de Keycloak/Core | Negacao de conexao, sem bypass | Teste de falha fechada |
| Motor com alerta de exploit | Isolamento, revogacao e reimplantacao limpa | Registro de incidente e restore |
| Corrupcao do banco/config do motor | Restaura em LAB sem credenciais produtivas | Tempo RPO/RTO medido |
| Agente offline/rollback | Nao mostrar falso online ou "sessao encerrada" sem confirmacao | Evidencia de timeout/estado incerto |

## 5. Gates de parada

**NO-GO:** a operacao remota segue BLOQUEADA ate aceite formal de TI/Seguranca e evidencias dos testes.

Nao liberar laboratório se a Infra nao souber isolar o motor, se nao houver backup **restaurado** em ambiente descartavel, se kill switch nao encerrar sessoes, se MFA/role revogadas mantiverem acesso ou se a mitigacao da vulnerabilidade do MeshCentral nao for demonstrada. Políticas de privacidade e auditoria exigem aprovacao humana.

**Estas sao instrucoes para planejamento e tabletop. Nenhum comando remoto, firewall, token, backup ou restauracao real foi executado.**
