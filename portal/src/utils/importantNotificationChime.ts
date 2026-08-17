/**
 * Soft attention chime for important notifications (Web Audio — no asset file).
 *
 * Chrome blocks AudioContext until a user gesture. We unlock on first
 * pointer/key/touch and replay any chime that was requested while suspended.
 */

let sharedContext: AudioContext | null = null;
let unlockListenersAttached = false;
let pendingChime = false;
let lastPlayedForId: string | null = null;

function getAudioContext(): AudioContext | null {
  if (typeof window === "undefined") return null;
  const Ctx =
    window.AudioContext ||
    (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!Ctx) return null;
  if (!sharedContext || sharedContext.state === "closed") {
    sharedContext = new Ctx();
  }
  return sharedContext;
}

function tone(
  ctx: AudioContext,
  frequency: number,
  startAt: number,
  duration: number,
  gainPeak: number,
): void {
  const oscillator = ctx.createOscillator();
  const gain = ctx.createGain();
  oscillator.type = "sine";
  oscillator.frequency.setValueAtTime(frequency, startAt);
  gain.gain.setValueAtTime(0.0001, startAt);
  gain.gain.exponentialRampToValueAtTime(gainPeak, startAt + 0.025);
  gain.gain.exponentialRampToValueAtTime(0.0001, startAt + duration);
  oscillator.connect(gain);
  gain.connect(ctx.destination);
  oscillator.start(startAt);
  oscillator.stop(startAt + duration + 0.03);
}

function emitChime(ctx: AudioContext): void {
  const t0 = ctx.currentTime + 0.01;
  tone(ctx, 587.33, t0, 0.16, 0.14);
  tone(ctx, 783.99, t0 + 0.12, 0.26, 0.11);
}

async function ensureRunningContext(): Promise<AudioContext | null> {
  const ctx = getAudioContext();
  if (!ctx) return null;
  try {
    if (ctx.state === "suspended") {
      await ctx.resume();
    }
    return ctx.state === "running" ? ctx : null;
  } catch {
    return null;
  }
}

async function flushPendingChime(): Promise<boolean> {
  if (!pendingChime) {
    await ensureRunningContext();
    return false;
  }
  const ctx = await ensureRunningContext();
  if (!ctx) return false;
  emitChime(ctx);
  pendingChime = false;
  return true;
}

function onUserGestureUnlock(): void {
  void flushPendingChime();
}

/** Call once from the authenticated shell so the first click unlocks audio. */
export function installImportantNotificationAudioUnlock(): void {
  if (typeof window === "undefined" || unlockListenersAttached) return;
  unlockListenersAttached = true;

  const opts: AddEventListenerOptions = { capture: true, passive: true };
  window.addEventListener("pointerdown", onUserGestureUnlock, opts);
  window.addEventListener("keydown", onUserGestureUnlock, opts);
  window.addEventListener("touchstart", onUserGestureUnlock, opts);
}

/**
 * Plays a short two-note chime. If autoplay is blocked, queues until the next
 * user gesture (then plays once).
 */
export async function playImportantNotificationChime(options?: {
  notificationId?: string;
}): Promise<void> {
  if (typeof window === "undefined") return;

  installImportantNotificationAudioUnlock();

  const notificationId = options?.notificationId;
  if (notificationId && lastPlayedForId === notificationId && !pendingChime) {
    return;
  }
  if (notificationId) {
    lastPlayedForId = notificationId;
  }

  pendingChime = true;
  const played = await flushPendingChime();
  if (!played) {
    pendingChime = true;
  }
}
