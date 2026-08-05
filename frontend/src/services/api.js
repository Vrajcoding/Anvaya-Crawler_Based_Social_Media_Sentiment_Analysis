import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const fetchStatsOverview = async () => {
  const res = await axios.get(`${API_BASE_URL}/stats/overview`);
  return res.data;
};

export const fetchPosts = async (params = {}) => {
  const res = await axios.get(`${API_BASE_URL}/posts`, { params });
  return res.data;
};

export const fetchAlerts = async (status = 'all') => {
  const res = await axios.get(`${API_BASE_URL}/alerts`, { params: { status } });
  return res.data;
};

export const acknowledgeAlert = async (alertId) => {
  const res = await axios.post(`${API_BASE_URL}/alerts/${alertId}/acknowledge`);
  return res.data;
};

export const resolveAlert = async (alertId) => {
  const res = await axios.post(`${API_BASE_URL}/alerts/${alertId}/resolve`);
  return res.data;
};

export const fetchTrendingHashtags = async () => {
  const res = await axios.get(`${API_BASE_URL}/trends/hashtags`);
  return res.data;
};

export const fetchTrendingKeywords = async () => {
  const res = await axios.get(`${API_BASE_URL}/trends/keywords`);
  return res.data;
};

export const fetchWatchlist = async () => {
  const res = await axios.get(`${API_BASE_URL}/watchlist`);
  return res.data;
};

export const addWatchlistItem = async (item) => {
  const res = await axios.post(`${API_BASE_URL}/watchlist`, item);
  return res.data;
};

export const deleteWatchlistItem = async (id) => {
  const res = await axios.delete(`${API_BASE_URL}/watchlist/${id}`);
  return res.data;
};

export const submitFeedback = async (feedbackData) => {
  const res = await axios.post(`${API_BASE_URL}/feedback`, feedbackData);
  return res.data;
};

export const generateReport = async (reportData) => {
  const res = await axios.post(`${API_BASE_URL}/reports/generate`, reportData);
  return res.data;
};

export const analyzeCustomText = async (textData) => {
  const res = await axios.post(`${API_BASE_URL}/posts/analyze`, textData);
  return res.data;
};
