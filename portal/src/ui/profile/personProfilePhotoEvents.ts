export const DELPI_PERSON_PROFILE_PHOTO_CHANGED_EVENT =
  "DELPI_PERSON_PROFILE_PHOTO_CHANGED";

/** Notify shell listeners (sidebar avatar) that the person-profile photo changed. */
export function notifyPersonProfilePhotoChanged(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(DELPI_PERSON_PROFILE_PHOTO_CHANGED_EVENT));
}
