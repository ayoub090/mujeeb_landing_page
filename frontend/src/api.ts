import axios from "axios";

// The production dashboard is served from usemujeeb.com while the API has its
// own public origin.  Falling back to localhost makes the browser call the
// visitor's computer instead of the VPS whenever the image was built without
// VITE_API_URL. Keep localhost only for local development.
const isLocalPreview = ["localhost", "127.0.0.1"].includes(window.location.hostname);
const localApiUrl = `http://${window.location.hostname}:8000`;
const defaultApiUrl = import.meta.env.DEV || isLocalPreview ? localApiUrl : "https://api.usemujeeb.com";
export const api = axios.create({baseURL: import.meta.env.VITE_API_URL || defaultApiUrl, withCredentials: true});
api.interceptors.response.use(undefined, async error => {
  const original = error.config;
  if (error.response?.status === 401 && !original?._retried && !original?.url?.includes("/refresh")) {
    original._retried = true;
    await api.post("/api/auth/refresh");
    return api(original);
  }
  return Promise.reject(error);
});
