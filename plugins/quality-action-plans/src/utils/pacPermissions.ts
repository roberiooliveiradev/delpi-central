import type { MeProfile } from "../api/meApi";
import {
  PAC_PERMISSION_ADMIN,
  PAC_PERMISSION_MANAGE,
  PAC_PERMISSION_VALIDATE_EFFECTIVENESS,
  PAC_PERMISSION_WRITE,
} from "../constants/permissions";

function profilePermissions(profile: MeProfile | null | undefined): Set<string> {
  return new Set(profile?.permissions ?? []);
}

function isSuperadmin(profile: MeProfile | null | undefined): boolean {
  return Boolean(profile?.is_superadmin);
}

function hasPermission(
  profile: MeProfile | null | undefined,
  permission: string,
): boolean {
  if (!profile) return false;
  if (isSuperadmin(profile)) return true;
  return profilePermissions(profile).has(permission);
}

function hasAnyPermission(
  profile: MeProfile | null | undefined,
  permissions: readonly string[],
): boolean {
  if (!profile) return false;
  if (isSuperadmin(profile)) return true;
  const granted = profilePermissions(profile);
  return permissions.some((permission) => granted.has(permission));
}

/** POST …/effectiveness-review/submit — `QUALITY_ACTION_PLANS_WRITE_PERMISSIONS`. */
export function canSubmitEffectivenessReview(
  profile: MeProfile | null | undefined,
): boolean {
  return hasAnyPermission(profile, [
    PAC_PERMISSION_WRITE,
    PAC_PERMISSION_MANAGE,
    PAC_PERMISSION_ADMIN,
  ]);
}

/** POST record/approve/reject e fila pendente — `QUALITY_ACTION_PLANS_VALIDATE_EFFECTIVENESS_PERMISSIONS`. */
export function canValidateEffectivenessReview(
  profile: MeProfile | null | undefined,
): boolean {
  return hasAnyPermission(profile, [
    PAC_PERMISSION_VALIDATE_EFFECTIVENESS,
    PAC_PERMISSION_MANAGE,
    PAC_PERMISSION_ADMIN,
  ]);
}

export function canWriteActionPlans(profile: MeProfile | null | undefined): boolean {
  return canSubmitEffectivenessReview(profile);
}

export function canManageActionPlans(profile: MeProfile | null | undefined): boolean {
  return hasAnyPermission(profile, [PAC_PERMISSION_MANAGE, PAC_PERMISSION_ADMIN]);
}

export function canReadActionPlans(profile: MeProfile | null | undefined): boolean {
  return (
    hasPermission(profile, "quality-action-plans.read")
    || canWriteActionPlans(profile)
    || canValidateEffectivenessReview(profile)
  );
}

export type EffectivenessUiPermissions = {
  canEditSection: boolean;
  canSaveDraft: boolean;
  canSubmit: boolean;
  canApprove: boolean;
  canReject: boolean;
  canRecordDirect: boolean;
  showRejectionReasonField: boolean;
};

export function resolveEffectivenessUiPermissions(input: {
  profile: MeProfile | null | undefined;
  isPendingApproval: boolean;
}): EffectivenessUiPermissions {
  const canSubmit = canSubmitEffectivenessReview(input.profile);
  const canValidate = canValidateEffectivenessReview(input.profile);
  const { isPendingApproval } = input;

  if (isPendingApproval) {
    return {
      canEditSection: canValidate,
      canSaveDraft: false,
      canSubmit: false,
      canApprove: canValidate,
      canReject: canValidate,
      canRecordDirect: false,
      showRejectionReasonField: canValidate,
    };
  }

  return {
    canEditSection: canSubmit || canValidate,
    canSaveDraft: canValidate,
    canSubmit: canSubmit,
    canApprove: false,
    canReject: false,
    canRecordDirect: canValidate,
    showRejectionReasonField: false,
  };
}
