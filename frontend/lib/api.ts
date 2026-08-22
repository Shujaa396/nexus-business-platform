const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  (process.env.NODE_ENV === "production" ? "/api/v1" : "http://localhost:8000/api/v1");

let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

function onRefreshed(token: string) {
  refreshSubscribers.forEach((callback) => callback(token));
  refreshSubscribers = [];
}

function addRefreshSubscriber(callback: (token: string) => void) {
  refreshSubscribers.push(callback);
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  accessToken?: string,
  isRetry = false,
): Promise<T> {
  const headers = new Headers(options.headers);

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // Get current access token
  const token =
    accessToken ??
    (typeof window !== "undefined"
      ? localStorage.getItem("nexus_access_token")
      : null);

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const url = `${API_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (error) {
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new Error(
        "Unable to connect to the NEXUS server. Make sure the backend is running.",
      );
    }
    throw error;
  }

  // If 401 Unauthorized, attempt token refresh unless this is already a refresh/login/register request
  if (
    response.status === 401 &&
    !isRetry &&
    !endpoint.includes("/auth/login") &&
    !endpoint.includes("/auth/register") &&
    !endpoint.includes("/auth/refresh") &&
    typeof window !== "undefined"
  ) {
    const refreshTokenValue = localStorage.getItem("nexus_refresh_token");

    if (refreshTokenValue) {
      if (!isRefreshing) {
        isRefreshing = true;
        try {
          const refreshRes = await fetch(`${API_URL}/auth/refresh`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshTokenValue }),
          });

          if (refreshRes.ok) {
            const data = await refreshRes.json();
            localStorage.setItem("nexus_access_token", data.access_token);
            localStorage.setItem("nexus_refresh_token", data.refresh_token);
            isRefreshing = false;
            onRefreshed(data.access_token);

            // Retry original request with new access token
            return apiRequest<T>(endpoint, options, data.access_token, true);
          } else {
            // Refresh token is invalid/expired
            isRefreshing = false;
            localStorage.removeItem("nexus_access_token");
            localStorage.removeItem("nexus_refresh_token");
            localStorage.removeItem("nexus_user");
            localStorage.removeItem("nexus_organization");
            window.location.href = "/login";
            throw new Error("Session expired. Please sign in again.");
          }
        } catch (err) {
          isRefreshing = false;
          throw err;
        }
      } else {
        // Wait for token refresh to complete
        return new Promise<T>((resolve, reject) => {
          addRefreshSubscriber((newToken: string) => {
            apiRequest<T>(endpoint, options, newToken, true)
              .then(resolve)
              .catch(reject);
          });
        });
      }
    }
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const data = await response.json();

      if (typeof data.detail === "string") {
        message = data.detail;
      } else if (Array.isArray(data.detail) && data.detail.length > 0) {
        message = data.detail
          .map((err: { msg?: string }) => err.msg || JSON.stringify(err))
          .join(", ");
      } else if (data.message && typeof data.message === "string") {
        message = data.message;
      }
    } catch {
      // Keep default error message
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export const api = {
  get: <T>(endpoint: string, options: RequestInit = {}) =>
    apiRequest<T>(endpoint, { ...options, method: "GET" }),
  post: <T>(endpoint: string, body?: unknown, options: RequestInit = {}) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),
  put: <T>(endpoint: string, body?: unknown, options: RequestInit = {}) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),
  patch: <T>(endpoint: string, body?: unknown, options: RequestInit = {}) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    }),
  delete: <T>(endpoint: string, options: RequestInit = {}) =>
    apiRequest<T>(endpoint, { ...options, method: "DELETE" }),
};

export { API_URL };