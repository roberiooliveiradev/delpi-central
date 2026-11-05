/** Tom visual semântico para variação MyWEG (aumento / redução / neutro). */
export type MyWegSemanticTone = "up" | "down" | "neutral" | "info";

export function toneFromSituation(situation: string): MyWegSemanticTone {
  switch (situation) {
    case "increased":
    case "appeared":
      return "up";
    case "decreased":
    case "disappeared":
      return "down";
    case "stable_with_date_changes":
      return "info";
    default:
      return "neutral";
  }
}

export function toneFromMovement(movement: string): MyWegSemanticTone {
  switch (movement) {
    case "increased":
      return "up";
    case "decreased":
      return "down";
    case "appeared":
      return "up";
    case "disappeared":
      return "down";
    default:
      return "neutral";
  }
}

export function movementBadgeClass(movement: string): string {
  const tone = toneFromMovement(movement);
  switch (tone) {
    case "up":
      return "ppc-myweg-needs__movement ppc-myweg-needs__movement--up";
    case "down":
      return "ppc-myweg-needs__movement ppc-myweg-needs__movement--down";
    case "info":
      return "ppc-myweg-needs__movement ppc-myweg-needs__movement--in";
    default:
      return "ppc-myweg-needs__movement";
  }
}

export function situationBadgeClass(situation: string): string {
  const tone = toneFromSituation(situation);
  switch (tone) {
    case "up":
      return "ppc-myweg-needs__movement ppc-myweg-needs__movement--up";
    case "down":
      return "ppc-myweg-needs__movement ppc-myweg-needs__movement--down";
    case "info":
      return "ppc-myweg-needs__movement ppc-myweg-needs__movement--in";
    default:
      return "ppc-myweg-needs__movement";
  }
}

export function deltaToneClass(situationOrMovement: string): string {
  const tone = toneFromSituation(situationOrMovement);
  if (tone === "neutral") {
    const fromMovement = toneFromMovement(situationOrMovement);
    if (fromMovement === "up") return "ppc-myweg-needs__delta ppc-myweg-needs__delta--up";
    if (fromMovement === "down") return "ppc-myweg-needs__delta ppc-myweg-needs__delta--down";
    return "ppc-myweg-needs__delta";
  }
  switch (tone) {
    case "up":
      return "ppc-myweg-needs__delta ppc-myweg-needs__delta--up";
    case "down":
      return "ppc-myweg-needs__delta ppc-myweg-needs__delta--down";
    default:
      return "ppc-myweg-needs__delta";
  }
}
