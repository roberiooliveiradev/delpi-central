# Homologação OTA — Production Pulse P4

Lab: 1 ESP flash USB na versão A → amarração firmware↔IoT → campanha → flash OTA para versão B sem USB.

## Pré-requisitos

- [ ] API com migration `V010` e volume `PP_FIRMWARE_UPLOAD_DIR`
- [ ] Device cadastrado com `device_api_token` e driver compatível
- [ ] IoT **amarrado** à família em `/apps/production-pulse/firmware-links` (1 IoT = 1 firmware)
- [ ] Sketch com `otaBaseUrl` = `http://<host>/apps/production-pulse-api`, `branch`, token
- [ ] Rede do ESP alcança o gateway em **HTTP**
- [ ] Binário novo com `FIRMWARE_VERSION` diferente (ex.: `…v1.3.0`)

## Passos

1. Flash USB versão **1.x**.
2. Admin: `POST /firmwares` (ou UI Firmwares) com binário **1.y**.
3. UI redireciona para amarração — ligue o IoT ao firmware (seta).
4. Admin: campanha `manual` (ou agendada).
5. Aguardar check do ESP (~1 min) ou reboot.
6. Confirmar target `updated` e `installedFirmwareVersion` = 1.y.
7. Negativo: publish sem job → `updateAvailable:false` (R52).
8. Negativo: token errado → 401.

## Evidência automatizada (sem VLAN)

```bash
cd production-pulse-api
pytest tests/test_firmware_ota_api.py tests/test_firmware_link_api.py tests/test_firmware_artifact_storage.py -q
cd ../plugins/production-pulse && npm test -- --run && npm run build
```

## Sketch — contrato

- Envelope: ler campos em `data` (`extractEnvelopeData`)
- Query: `controllerCode` / `branch` URL-encoded
- Reports HTTP finalizados antes do download do artefato

## Resultado

| Item | Status |
|------|--------|
| API canal device + firmware-link | pytest |
| MFE catálogo/campanhas/canvas | vitest + build |
| Sketch check/download/report | código + lab opcional |
| R52–R60 canônico | API-ROUTES ✅ |
