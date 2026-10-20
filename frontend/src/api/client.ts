import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import type { QueryClient } from "@tanstack/react-query";
import { useAuthStore } from "../store/auth";
import type {
  Entry,
  Kind,
  Level,
  Product,
  ProductInput,
  ReleaseVersion,
  SessionPayload,
} from "./types";

export const apiBase = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

export const client = axios.create({ baseURL: apiBase });

type RetryConfig = InternalAxiosRequestConfig & { _retry?: boolean };

let refreshTask: Promise<string | null> | null = null;

async function requestNewAccess(): Promise<string | null> {
  const refresh = useAuthStore.getState().refresh;
  if (!refresh) return null;
  try {
    const response = await axios.post<{ access: string }>(`${apiBase}/api/auth/token/refresh/`, { refresh });
    useAuthStore.setState({ access: response.data.access });
    return response.data.access;
  } catch {
    useAuthStore.getState().clear();
    return null;
  }
}

function refreshAccess(): Promise<string | null> {
  refreshTask ??= requestNewAccess().finally(() => {
    refreshTask = null;
  });
  return refreshTask;
}

function skipsAuth(url: string): boolean {
  return url.includes("/api/auth/token/") || url.includes("/api/auth/register/") || url.includes("/api/health/");
}

client.interceptors.request.use((config) => {
  const access = useAuthStore.getState().access;
  if (access && !skipsAuth(config.url ?? "")) {
    config.headers.set("Authorization", `Bearer ${access}`);
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetryConfig | undefined;
    const url = original?.url ?? "";
    if (error.response?.status === 401 && original && !original._retry && !url.includes("/api/auth/token/")) {
      original._retry = true;
      const access = await refreshAccess();
      if (!access) return Promise.reject(error);
      original.headers.set("Authorization", `Bearer ${access}`);
      return client(original);
    }
    return Promise.reject(error);
  },
);

export function invalidateRelease(queryClient: QueryClient, productId: string, versionId?: string) {
  const jobs = [
    queryClient.invalidateQueries({ queryKey: ["products"] }),
    queryClient.invalidateQueries({ queryKey: ["product", productId] }),
    queryClient.invalidateQueries({ queryKey: ["entries", productId] }),
    queryClient.invalidateQueries({ queryKey: ["versions", productId] }),
    queryClient.invalidateQueries({ queryKey: ["changelog", productId] }),
  ];
  if (versionId) {
    jobs.push(queryClient.invalidateQueries({ queryKey: ["version", versionId] }));
  }
  return Promise.all(jobs);
}

export const api = {
  products: {
    list: () => client.get<Product[]>("/api/products/").then((response) => response.data),
    get: (id: string) => client.get<Product>(`/api/products/${id}/`).then((response) => response.data),
    create: (body: ProductInput) => client.post<Product>("/api/products/", body).then((response) => response.data),
    update: (id: string, body: ProductInput) =>
      client.patch<Product>(`/api/products/${id}/`, body).then((response) => response.data),
    remove: (id: string) => client.delete(`/api/products/${id}/`),
    changelog: (id: string) =>
      client.get<{ markdown: string }>(`/api/products/${id}/changelog/`).then((response) => response.data.markdown),
    bump: (id: string, body: { level: Level; prerelease?: string }) =>
      client.post<ReleaseVersion>(`/api/products/${id}/bump/`, body).then((response) => response.data),
  },
  versions: {
    list: (productId: string) =>
      client
        .get<ReleaseVersion[]>("/api/versions/", { params: { product: productId } })
        .then((response) => response.data),
    get: (id: string) => client.get<ReleaseVersion>(`/api/versions/${id}/`).then((response) => response.data),
    updateChecklist: (id: string, body: Partial<Pick<ReleaseVersion["checklist"], "tests" | "notes" | "tag">>) =>
      client.patch<ReleaseVersion>(`/api/versions/${id}/checklist/`, body).then((response) => response.data),
    publish: (id: string) =>
      client.post<ReleaseVersion>(`/api/versions/${id}/publish/`).then((response) => response.data),
    remove: (id: string) => client.delete(`/api/versions/${id}/`),
  },
  entries: {
    list: (params: { product: string; bucket?: "unreleased"; version?: string }) =>
      client.get<Entry[]>("/api/entries/", { params }).then((response) => response.data),
    create: (body: { product: number; version?: number | null; kind: Kind; text: string }) =>
      client.post<Entry>("/api/entries/", body).then((response) => response.data),
    update: (id: number, body: Partial<{ kind: Kind; text: string }>) =>
      client.patch<Entry>(`/api/entries/${id}/`, body).then((response) => response.data),
    remove: (id: number) => client.delete(`/api/entries/${id}/`),
  },
  auth: {
    login: (username: string, password: string) =>
      client
        .post<{ access: string; refresh: string }>("/api/auth/token/", { username, password })
        .then((response) => response.data),
    register: (username: string, password: string) =>
      client
        .post<SessionPayload>("/api/auth/register/", { username, password })
        .then((response) => response.data),
    me: () => client.get<{ id: number; username: string }>("/api/auth/me/").then((response) => response.data),
  },
};
