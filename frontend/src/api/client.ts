import axios, { AxiosError } from "axios";
import type { ApiError } from "@/types";

/**
 * Central axios instance.
 *
 * In development the Vite proxy rewrites /api → http://localhost:8000, so
 * every request only needs to hit `/api/...`.  In production set
 * VITE_API_BASE_URL to the real backend origin.
 */
export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL
    ? `${import.meta.env.VITE_API_BASE_URL}`
    : "/api",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30_000,
});

// ─── Response interceptor: normalise errors ───────────────────────────────────

http.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const apiError: ApiError = {
      detail:
        error.response?.data?.detail ??
        error.message ??
        "An unexpected error occurred",
      status: error.response?.status ?? 0,
    };
    return Promise.reject(apiError);
  }
);
