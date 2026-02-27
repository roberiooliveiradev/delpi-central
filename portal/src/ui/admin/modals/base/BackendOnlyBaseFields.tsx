// src/ui/admin/modals/base/BackendOnlyBaseFields.tsx

import { AccordionSection } from "../../../../components/AccordionSection";
import { FormField } from "../../../../components/FormField";

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
    {/* =========================
        CONFIGURAÇÃO DO SERVIÇO
    ========================== */}
    <AccordionSection
      title="Configuração do Serviço"
      icon="Server"
      defaultOpen
      forceOpen={hasSectionError("backend")}
      hasError={hasSectionError("backend")}
    >
      <FormField label="Nome do Serviço">
        <input
          value={backend.serviceName || ""}
          onChange={(e) =>
            setNested("backend", { serviceName: e.target.value })
          }
          placeholder="ex: api-delpi"
        />
      </FormField>

      <FormField label="Base URL do Serviço">
        <input
          value={backend.baseUrl || ""}
          onChange={(e) =>
            setNested("backend", { baseUrl: e.target.value })
          }
          placeholder="/apps/api-delpi"
        />
      </FormField>

      <FormField label="Serviço é obrigatório?">
        <select
          value={backend.required ? "true" : "false"}
          onChange={(e) =>
            setNested("backend", { required: e.target.value === "true" })
          }
        >
          <option value="true">Sim</option>
          <option value="false">Não</option>
        </select>
      </FormField>

      <FormField label="Validar JWT">
        <select
          value={backend.validateJwt ? "true" : "false"}
          onChange={(e) =>
            setNested("backend", { validateJwt: e.target.value === "true" })
          }
        >
          <option value="true">Sim</option>
          <option value="false">Não</option>
        </select>
      </FormField>

      <FormField label="Audience (JWT)">
        <input
          value={backend.audience || ""}
          onChange={(e) =>
            setNested("backend", { audience: e.target.value })
          }
          placeholder="delpi-central"
        />
      </FormField>

      <FormField label="Issuer (JWT)">
        <input
          value={backend.issuer || ""}
          onChange={(e) =>
            setNested("backend", { issuer: e.target.value })
          }
          placeholder="https://central.delpi.com.br/auth/realms/delpi"
        />
      </FormField>

      <FormField label="Header de Permissões">
        <input
          value={backend.requiredPermissionsHeader || ""}
          onChange={(e) =>
            setNested("backend", {
              requiredPermissionsHeader: e.target.value,
            })
          }
          placeholder="x-user-permissions"
        />
      </FormField>
    </AccordionSection>

    {/* =========================
        CICLO DE VIDA
    ========================== */}
    <AccordionSection
      title="Ciclo de Vida"
      icon="RefreshCcw"
      forceOpen={hasSectionError("lifecycle")}
      hasError={hasSectionError("lifecycle")}
    >
      <FormField label="Permitir Hot Reload">
        <select
          value={lifecycle.allowHotReload ? "true" : "false"}
          onChange={(e) =>
            setNested("lifecycle", {
              allowHotReload: e.target.value === "true",
            })
          }
        >
          <option value="true">Sim</option>
          <option value="false">Não</option>
        </select>
      </FormField>

      <FormField label="Permitir Atualização de Versão">
        <select
          value={lifecycle.allowVersionUpgrade ? "true" : "false"}
          onChange={(e) =>
            setNested("lifecycle", {
              allowVersionUpgrade: e.target.value === "true",
            })
          }
        >
          <option value="true">Sim</option>
          <option value="false">Não</option>
        </select>
      </FormField>

      <FormField label="Criar Rotas Automaticamente">
        <select
          value={lifecycle.autoCreateRoutes ? "true" : "false"}
          onChange={(e) =>
            setNested("lifecycle", {
              autoCreateRoutes: e.target.value === "true",
            })
          }
        >
          <option value="true">Sim</option>
          <option value="false">Não</option>
        </select>
      </FormField>

      <FormField label="Registrar Permissões Automaticamente">
        <select
          value={lifecycle.autoRegisterPermissions ? "true" : "false"}
          onChange={(e) =>
            setNested("lifecycle", {
              autoRegisterPermissions: e.target.value === "true",
            })
          }
        >
          <option value="true">Sim</option>
          <option value="false">Não</option>
        </select>
      </FormField>
    </AccordionSection>

    {/* =========================
        SEGURANÇA
    ========================== */}
    <AccordionSection
      title="Segurança"
      icon="Shield"
      forceOpen={hasSectionError("security")}
      hasError={hasSectionError("security")}
    >
      <FormField label="Exigir HTTPS">
        <select
          value={security.requireHttps ? "true" : "false"}
          onChange={(e) =>
            setNested("security", {
              requireHttps: e.target.value === "true",
            })
          }
        >
          <option value="true">Sim</option>
          <option value="false">Não</option>
        </select>
      </FormField>
    </AccordionSection>

    {/* =========================
        OBSERVABILIDADE
    ========================== */}
    <AccordionSection
      title="Observabilidade"
      icon="Activity"
      forceOpen={hasSectionError("observability")}
      hasError={hasSectionError("observability")}
    >
      <FormField label="Endpoint de Health Check">
        <input
          value={observability.healthEndpoint || ""}
          onChange={(e) =>
            setNested("observability", {
              healthEndpoint: e.target.value,
            })
          }
          placeholder="/health"
        />
      </FormField>

      <FormField label="Formato de Log">
        <input
          value={observability.logFormat || ""}
          onChange={(e) =>
            setNested("observability", {
              logFormat: e.target.value,
            })
          }
          placeholder="json"
        />
      </FormField>
    </AccordionSection>

    {/* =========================
        INTERFACE
    ========================== */}
    <AccordionSection
      title="Interface"
      icon="Monitor"
      forceOpen={hasSectionError("ui")}
      hasError={hasSectionError("ui")}
    >
      <FormField label="Exibir no App Launcher">
        <select
          value={ui.displayInAppLauncher ? "true" : "false"}
          onChange={(e) =>
            setNested("ui", {
              displayInAppLauncher: e.target.value === "true",
            })
          }
        >
          <option value="true">Sim</option>
          <option value="false">Não</option>
        </select>
      </FormField>
    </AccordionSection>
  </>
);
};