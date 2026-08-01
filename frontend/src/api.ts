import axios from "axios";

export const api = axios.create({baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000", withCredentials: true});
api.interceptors.response.use(undefined, async error => {
  const original = error.config;
  if (error.response?.status === 401 && !original?._retried && !original?.url?.includes("/refresh")) {
    original._retried = true;
    await api.post("/api/auth/refresh");
    return api(original);
  }
  return Promise.reject(error);
});
