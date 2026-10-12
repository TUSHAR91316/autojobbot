import axios from "axios";

// Strictly bound to loopback FastAPI backend
export const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});
