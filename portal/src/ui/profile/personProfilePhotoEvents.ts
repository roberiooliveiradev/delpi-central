/** Fired when cargo/contatos or photo change — MFEs listen with the same string. */
export const DELPI_PERSON_PROFILE_CHANGED_EVENT = "DELPI_PERSON_PROFILE_CHANGED";

export const DELPI_PERSON_PROFILE_PHOTO_CHANGED_EVENT =
  "DELPI_PERSON_PROFILE_PHOTO_CHANGED";

/** Notify listeners that person-profile fields (cargo/contatos) changed. */
export function notifyPersonProfileChanged(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(DELPI_PERSON_PROFILE_CHANGED_EVENT));
}

/** Notify shell listeners (sidebar avatar) that the person-profile photo changed. */
export function notifyPersonProfilePhotoChanged(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(DELPI_PERSON_PROFILE_PHOTO_CHANGED_EVENT));
  notifyPersonProfileChanged();
}
