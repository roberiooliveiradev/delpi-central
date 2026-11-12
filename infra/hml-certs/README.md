# Certificados TLS da homologação (fora do Git)

Este diretório recebe a CA e o certificado de servidor gerados por
`infra/scripts/hml-tls-prepare.sh`.

- **Não** versionar `.key`, `.pem`, `.crt` nem bundles.
- **Não** reutilizar certificados de produção.
- Confiança nos PCs de teste: instalar a CA local (`hml-local-ca.crt`) no
  store corporativo/usuário (Windows: “Autoridades de Certificação Raiz
  Confiáveis”; Linux/Firefox: store do SO/navegador).
- Ativação do listener HTTPS HML exige autorização explícita; o script
  `hml-compose.sh` **não** sobe TLS automaticamente nesta fase.
