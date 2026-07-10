/**
 * Side-effect: registra React/lucide em __federation_shared__ na carga do módulo.
 *
 * Deve ser o **primeiro** import em bootstrap.tsx dos MFEs federados — imports
 * estáticos de App/páginas puxam @delpi/plugin-ui antes do await preparePluginUiRemote().
 */
import { ensureMfeFederationShareScope } from "./federationShareScope";

ensureMfeFederationShareScope();
