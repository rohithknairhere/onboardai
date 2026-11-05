// Where the website finds the backend. Local development talks to the FastAPI
// server on port 8000; the hosted build sets VITE_API_URL=/api because the
// backend serves the website itself from the same address.
export const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api';
