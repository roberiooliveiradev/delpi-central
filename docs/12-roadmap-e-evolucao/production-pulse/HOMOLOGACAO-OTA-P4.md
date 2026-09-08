# Homologação OTA — Production Pulse P4

Lab: 1 ESP flash USB na versão A → campanha → flash OTA para versão B sem USB.

## Pré-requisitos

- [ ] API com migration `V010` e volume `PP_FIRMWARE_UPLOAD_DIR`
- [ ] Device cadastrado com `device_api_token` e `driver_key`/`firmware_key` alinhados
- [ ] Sketch com `otaBaseUrl` + `branch` + token (EEPROM)
- [ ] Rede do ESP alcança o gateway (`/apps/production-pulse-api`)

## Passos

1. Flash USB versão **1.x** (`FIRMWARE_VERSION` no sketch).
2. Admin: `POST /firmwares` com binário **1.y** (mesmo `firmwareKey`).
3. Admin: job `manual` (ou agendado no passado) para o device.
4. Aguardar check do ESP (ou forçar reboot e esperar ~1 min).
5. Confirmar target `updated`, `installedFirmwareVersion` = 1.y no detalhe.
6. Negativo: publicar sem job → check retorna `updateAvailable:false` (R52).
7. Negativo: token errado → 401 no `/device-ota/check`.

## Evidência automatizada (sem VLAN)

```bash
cd production-pulse-api
pytest tests/test_firmware_ota_api.py tests/test_firmware_artifact_storage.py -q
cd ../plugins/production-pulse && npm test -- --run && npm run build
```

## Resultado

| Item | Status |
|------|--------|
| API canal device R52–R58 | pytest |
| MFE catálogo/campanhas/KPI | vitest + build |
| Sketch check/download/report | código + lab opcional |
| R52–R60 canônico | API-ROUTES ✅ |
