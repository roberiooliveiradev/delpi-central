import type { BranchCode } from "../constants/branch";

export function branchRoom(branch: BranchCode): string {
  return `lnf:branch:${branch}`;
}

export function requestRoom(requestId: string): string {
  return `lnf:request:${requestId.trim()}`;
}

export function unmappedProductsRoom(): string {
  return "lnf:unmapped-products";
}

export function encodeLnfSubscribe(room: string): string {
  return JSON.stringify({ type: "subscribe", room });
}

export function encodeLnfUnsubscribe(room: string): string {
  return JSON.stringify({ type: "unsubscribe", room });
}
