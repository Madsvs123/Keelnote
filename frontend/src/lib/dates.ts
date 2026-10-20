import { format, formatDistanceToNow, parseISO } from "date-fns";

export function formatDay(value: string): string {
  const [year, month, day] = value.split("-").map(Number);
  return format(new Date(year, (month || 1) - 1, day || 1), "d MMM yyyy");
}

export function formatAgo(value: string): string {
  return formatDistanceToNow(parseISO(value), { addSuffix: true });
}
