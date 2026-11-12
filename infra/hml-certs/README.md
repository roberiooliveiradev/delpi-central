# Certificados TLS da homologação (fora do Git)

Este diretório recebe a CA e o certificado de servidor gerados por
`infra/scripts/hml-tls-prepare.sh`.

## Arquivos esperados

| Arquivo | Uso |
|---|---|
| `hml-local-ca.crt` | CA pública — instalar nos PCs de teste autorizados |
| `hml-local-ca.key` | Chave da CA — **não** montar no gateway; custódia segura |
| `hml-gateway.crt` | Certificado do servidor (SAN `IP:192.168.1.237`) |
| `hml-gateway.key` | Chave do servidor — montada só no container gateway HML |

## Regras

- **Não** versionar `.key`, `.pem`, `.crt` nem bundles.
- **Não** reutilizar certificados de produção.
- **Não** copiar a chave da CA para o gateway.
- Confiança nos PCs de teste: instalar `hml-local-ca.crt` no store
  corporativo/usuário (Windows: “Autoridades de Certificação Raiz
  Confiáveis”; Linux/Firefox: store do SO/navegador).
- Endpoint canônico: `https://192.168.1.237:18443`
- HTTP `:18080` permanece só para health/rollback — login browser exige HTTPS.

## Geração

```bash
./infra/scripts/hml-tls-prepare.sh --host 192.168.1.237
```

Após backup da chave da CA em custódia autorizada, remover
`hml-local-ca.key` da VM quando o processo de TI confirmar.
