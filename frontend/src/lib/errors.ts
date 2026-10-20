import axios from "axios";

export function errorText(error: unknown, fallback: string): string {
  if (!axios.isAxiosError(error)) return fallback;
  const data = error.response?.data;
  if (!data) return fallback;
  if (typeof data === "string") return data;
  if (typeof data === "object" && data && "detail" in data && typeof data.detail === "string") {
    return data.detail;
  }
  if (typeof data === "object" && data) {
    const parts: string[] = [];
    for (const [key, value] of Object.entries(data as Record<string, unknown>)) {
      const message = Array.isArray(value) ? value.map(String).join(" ") : String(value);
      parts.push(key === "non_field_errors" || key === "detail" ? message : `${key}: ${message}`);
    }
    if (parts.length) return parts.join(" ");
  }
  return fallback;
}
