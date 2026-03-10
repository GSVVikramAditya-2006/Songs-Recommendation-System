import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});

export const searchSongs = (q, limit = 20) =>
  api.get("/songs/search", { params: { q, limit } }).then((r) => r.data);

export const getAllSongs = (limit = 50, offset = 0) =>
  api.get("/songs/all", { params: { limit, offset } }).then((r) => r.data);

export const getSong = (songId) =>
  api.get(`/songs/${songId}`).then((r) => r.data);

export const getRecommendations = (songId, userId = null, n = 10) =>
  api.post("/recommend", { song_id: songId, user_id: userId, n }).then((r) => r.data);

export const rateSong = (userId, songId, rating) =>
  api.post("/recommend/rate", { user_id: userId, song_id: songId, rating }).then((r) => r.data);

export const getHistory = (userId) =>
  api.get(`/recommend/history/${userId}`).then((r) => r.data);

export default api;
