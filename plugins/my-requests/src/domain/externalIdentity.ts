/**
 * Identidades externas gravadas pelo Requests API (P1/P2).
 *
 * `operator:<filial>:<codigo>` identifica um operador do cockpit público —
 * não é um usuário do Portal/Minha DELPI. Esses IDs nunca devem ser enviados
 * para lookups de participantes/avatar da Core (retornariam 404 e gerariam
 * tráfego inútil); a apresentação usa nome + avatar por iniciais.
 */

export const EXTERNAL_OPERATOR_ID_PREFIX = "operator:";

export function isExternalOperatorId(
  value: string | null | undefined,
): boolean {
  return (value ?? "").trim().startsWith(EXTERNAL_OPERATOR_ID_PREFIX);
}
