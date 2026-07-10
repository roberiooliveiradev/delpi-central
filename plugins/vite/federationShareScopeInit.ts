/**
 * @deprecated Use `await import("./App")` após `preparePluginUiRemote()` no bootstrap.
 * Side-effect só no build — o bundler MF deduplica e executa tarde demais (React #321).
 * Ver plugins/plugin-ui/docs/module-federation.md § Bootstrap.
 */
import { ensureMfeFederationShareScope } from "./federationShareScope";

ensureMfeFederationShareScope();
