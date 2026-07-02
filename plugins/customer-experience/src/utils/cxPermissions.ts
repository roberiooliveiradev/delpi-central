import type { MeProfile } from "../api/meApi";
import {
  CX_ADMIN,
  CX_FORMS_MANAGE,
  CX_FORMS_READ,
  CX_FORMS_WRITE,
  CX_PARTICIPANTS_MANAGE,
  CX_PARTICIPANTS_READ,
  CX_PARTICIPANTS_WRITE,
} from "../constants/permissions";

function granted(profile: MeProfile | null | undefined): Set<string> {
  return new Set(profile?.permissions ?? []);
}

function isSuperadmin(profile: MeProfile | null | undefined): boolean {
  return Boolean(profile?.is_superadmin);
}

function isAdmin(profile: MeProfile | null | undefined): boolean {
  return isSuperadmin(profile) || granted(profile).has(CX_ADMIN);
}

function hasAny(
  profile: MeProfile | null | undefined,
  permissions: readonly string[],
): boolean {
  if (!profile) return false;
  if (isAdmin(profile)) return true;
  const set = granted(profile);
  return permissions.some((permission) => set.has(permission));
}

export function canReadParticipants(profile: MeProfile | null | undefined): boolean {
  return hasAny(profile, [
    CX_PARTICIPANTS_READ,
    CX_PARTICIPANTS_WRITE,
    CX_PARTICIPANTS_MANAGE,
  ]);
}

export function canWriteParticipants(profile: MeProfile | null | undefined): boolean {
  return hasAny(profile, [CX_PARTICIPANTS_WRITE, CX_PARTICIPANTS_MANAGE]);
}

export function canManageParticipants(profile: MeProfile | null | undefined): boolean {
  return hasAny(profile, [CX_PARTICIPANTS_MANAGE]);
}

export function canReadForms(profile: MeProfile | null | undefined): boolean {
  return hasAny(profile, [CX_FORMS_READ, CX_FORMS_WRITE, CX_FORMS_MANAGE]);
}

export function canWriteForms(profile: MeProfile | null | undefined): boolean {
  return hasAny(profile, [CX_FORMS_WRITE, CX_FORMS_MANAGE]);
}

export function canManageForms(profile: MeProfile | null | undefined): boolean {
  return hasAny(profile, [CX_FORMS_MANAGE]);
}
