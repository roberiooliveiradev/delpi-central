import { buildPluginPath, buildUserProfileHref } from "../../app/pluginRoutes";
import { USER_PROFILE_CONTENT } from "./userProfileContent";

/**
 * Canonical self-profile href: the portal user profile opened from shell
 * surfaces (TopBar avatar) carries a safe `returnTo` back to the Supplies home.
 */
export function buildSelfProfileHref(userId: string, basePath: string): string {
  const returnTo = buildPluginPath("home", basePath);
  const params = new URLSearchParams();
  params.set("returnTo", returnTo);
  params.set("returnLabel", USER_PROFILE_CONTENT.backFallback);
  return buildUserProfileHref(userId, basePath, `?${params.toString()}`);
}
