// src/ui/admin/modals/base/BackendOnlyBaseFields.tsx

import { AccordionSection } from "../../../../components/AccordionSection";
import { FormField, FormGrid, Input, Switch } from "../../../../ui-kit";

type Props = {
  manifest: any;
  setBase: (patch: any) => void;
  errorsByPath: Map<string, string[]>;
};

export const BackendOnlyBaseFields = ({
  manifest,
  setBase,
  errorsByPath,
}: Props) => {
  const backend = manifest.backend || {};
  const lifecycle = manifest.lifecycle || {};
  const security = manifest.security || {};
  const observability = manifest.observability || {};
  const ui = manifest.ui || {};

  const setNested = (key: string, value: any) => {
    setBase({
      [key]: {
        ...manifest[key],
        ...value,
      },
    });
  };

  const hasSectionError = (prefix: string) => {
    for (const key of errorsByPath.keys()) {
      if (key.startsWith(prefix)) return true;
    }
    return false;
  };

  return (
    <>
      <AccordionSection
        title="Configuração do Serviço"
        icon="Server"
        defaultOpen
        forceOpen={hasSectionError("backend")}
        hasError={hasSectionError("backend")}
      >
        <FormGrid columns={2}>
          <FormField label="Nome do Serviço" htmlFor="backend-service-name">
            <Input
              value={backend.serviceName || ""}
              onChange={(e) =>
                setNested("backend", { serviceName: e.target.value })
              }
              placeholder="ex: api-delpi"
            />
          </FormField>

          <FormField label="Base URL do Serviço" htmlFor="backend-base-url">
            <Input
              value={backend.baseUrl || ""}
              onChange={(e) => setNested("backend", { baseUrl: e.target.value })}
              placeholder="/apps/api-delpi"
              mono
            />
          </FormField>

          <FormField label="Audience (JWT)" htmlFor="backend-audience">
            <Input
              value={backend.audience || ""}
              onChange={(e) =>
                setNested("backend", { audience: e.target.value })
              }
              placeholder="delpi-central"
            />
          </FormField>

          <FormField label="Issuer (JWT)" htmlFor="backend-issuer">
            <Input
              value={backend.issuer || ""}
              onChange={(e) => setNested("backend", { issuer: e.target.value })}
              placeholder="https://central.delpi.com.br/auth/realms/delpi"
              mono
            />
          </FormField>

          <FormField
            label="Header de Permissões"
            htmlFor="backend-permissions-header"
          >
            <Input
              value={backend.requiredPermissionsHeader || ""}
              onChange={(e) =>
                setNested("backend", {
                  requiredPermissionsHeader: e.target.value,
                })
              }
              placeholder="x-user-permissions"
              mono
            />
          </FormField>
        </FormGrid>

        <div className="portal-ui-switch-row">
          <Switch
            checked={!!backend.required}
            onChange={(e) =>
              setNested("backend", { required: e.target.checked })
            }
            label="Serviço é obrigatório"
          />

          <Switch
            checked={!!backend.validateJwt}
            onChange={(e) =>
              setNested("backend", { validateJwt: e.target.checked })
            }
            label="Validar JWT"
          />
        </div>
      </AccordionSection>

      <AccordionSection
        title="Ciclo de Vida"
        icon="RefreshCcw"
        forceOpen={hasSectionError("lifecycle")}
        hasError={hasSectionError("lifecycle")}
      >
        <div className="portal-ui-switch-row">
          <Switch
            checked={!!lifecycle.allowHotReload}
            onChange={(e) =>
              setNested("lifecycle", { allowHotReload: e.target.checked })
            }
            label="Permitir hot reload"
          />

          <Switch
            checked={!!lifecycle.allowVersionUpgrade}
            onChange={(e) =>
              setNested("lifecycle", { allowVersionUpgrade: e.target.checked })
            }
            label="Permitir atualização de versão"
          />

          <Switch
            checked={!!lifecycle.autoCreateRoutes}
            onChange={(e) =>
              setNested("lifecycle", { autoCreateRoutes: e.target.checked })
            }
            label="Criar rotas automaticamente"
          />

          <Switch
            checked={!!lifecycle.autoRegisterPermissions}
            onChange={(e) =>
              setNested("lifecycle", {
                autoRegisterPermissions: e.target.checked,
              })
            }
            label="Registrar permissões automaticamente"
          />
        </div>
      </AccordionSection>

      <AccordionSection
        title="Segurança"
        icon="Shield"
        forceOpen={hasSectionError("security")}
        hasError={hasSectionError("security")}
      >
        <div className="portal-ui-switch-row">
          <Switch
            checked={!!security.requireHttps}
            onChange={(e) =>
              setNested("security", { requireHttps: e.target.checked })
            }
            label="Exigir HTTPS"
          />
        </div>
      </AccordionSection>

      <AccordionSection
        title="Observabilidade"
        icon="Activity"
        forceOpen={hasSectionError("observability")}
        hasError={hasSectionError("observability")}
      >
        <FormGrid columns={2}>
          <FormField
            label="Endpoint de Health Check"
            htmlFor="observability-health"
          >
            <Input
              value={observability.healthEndpoint || ""}
              onChange={(e) =>
                setNested("observability", { healthEndpoint: e.target.value })
              }
              placeholder="/health"
              mono
            />
          </FormField>

          <FormField label="Formato de Log" htmlFor="observability-log-format">
            <Input
              value={observability.logFormat || ""}
              onChange={(e) =>
                setNested("observability", { logFormat: e.target.value })
              }
              placeholder="json"
            />
          </FormField>
        </FormGrid>
      </AccordionSection>

      <AccordionSection
        title="Interface"
        icon="Monitor"
        forceOpen={hasSectionError("ui")}
        hasError={hasSectionError("ui")}
      >
        <div className="portal-ui-switch-row">
          <Switch
            checked={!!ui.displayInAppLauncher}
            onChange={(e) =>
              setNested("ui", { displayInAppLauncher: e.target.checked })
            }
            label="Exibir no App Launcher"
          />
        </div>
      </AccordionSection>
    </>
  );
};
