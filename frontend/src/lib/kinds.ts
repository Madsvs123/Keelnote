import { Minus, Pencil, Plus, Wrench, type LucideIcon } from "lucide-react";
import type { Kind } from "../api/types";

export const KIND_ORDER: Kind[] = ["added", "changed", "fixed", "removed"];

export const KIND_META: Record<Kind, { label: string; icon: LucideIcon }> = {
  added: { label: "Added", icon: Plus },
  changed: { label: "Changed", icon: Pencil },
  fixed: { label: "Fixed", icon: Wrench },
  removed: { label: "Removed", icon: Minus },
};
