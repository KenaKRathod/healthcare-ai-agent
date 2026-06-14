// In dev, Vite proxies API routes to the FastAPI backend (see vite.config.js).
// Set VITE_API_BASE_URL for production builds, e.g. http://localhost:8000
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";


// Retrieve the token from localStorage
export const getToken = () => localStorage.getItem("token");
export const getRole = () => localStorage.getItem("role");
export const getUsername = () => localStorage.getItem("username");

// Save auth data
export const setAuthData = (token, role, username) => {
  localStorage.setItem("token", token);
  localStorage.setItem("role", role);
  localStorage.setItem("username", username);
};

// Clear auth data on logout
export const logout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("username");
  window.location.href = "/";
};

// Generic request wrapper with Authorization header injection and 401 interceptor
async function request(endpoint, options = {}) {
  const token = getToken();
  const headers = {
    ...options.headers,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Handle file uploads (Multipart Form Data)
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

    if (response.status === 401) {
      // Session expired or invalid
      logout();
      throw new Error("Session expired. Please log in again.");
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.error || "An error occurred");
    }

    return await response.json();
  } catch (error) {
    console.error(`API request failed at ${endpoint}:`, error);
    if (error instanceof TypeError) {
      const targetUrl = `${API_BASE_URL}${endpoint}`;
      throw new Error(
        `Cannot reach backend at '${targetUrl}'. If this is a live deployment, ensure you have set the VITE_API_BASE_URL environment variable in your Vercel project settings (e.g., https://your-backend.onrender.com) and redeployed the frontend. For local development, make sure the backend server is running.`
      );
    }
    throw error;
  }
}

// Authentication API
export const authAPI = {
  login: async (username, password) => {
    const data = await request("/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    setAuthData(data.access_token, data.role, data.username);
    return data;
  },
  register: async (username, password, role) => {
    return request("/register", {
      method: "POST",
      body: JSON.stringify({ username, password, role }),
    });
  },
  getMe: async () => {
    return request("/me", { method: "GET" });
  },
};

// Health Records API
export const healthAPI = {
  getRecords: async (limit = 20) => {
    return request(`/health-data?limit=${limit}`, { method: "GET" });
  },
  addRecord: async (recordData) => {
    // Convert object properties to query string since add_health_data takes query parameters
    const params = new URLSearchParams();
    Object.entries(recordData).forEach(([key, val]) => {
      if (val !== undefined && val !== null) {
        params.append(key, val);
      }
    });
    return request(`/health-data?${params.toString()}`, {
      method: "POST",
    });
  },
  uploadDataset: async (file, patientName, question = "Summarize my health trends and risks.", format = "json") => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("patient_name", patientName);
    formData.append("question", question);
    formData.append("report_format", format);

    return request("/upload-health-data", {
      method: "POST",
      body: formData,
    });
  },
};

// Goals API
export const goalsAPI = {
  getGoals: async (patientName, steps = 0, sleep = 0, weightLoss = 0) => {
    return request(
      `/health-goals?patient_name=${encodeURIComponent(patientName)}&steps=${steps}&sleep_hours=${sleep}&weight_loss_progress_kg=${weightLoss}`,
      { method: "GET" }
    );
  },
  createGoal: async (patientName, goalName, targetValue, unit = "") => {
    return request("/health-goals", {
      method: "POST",
      body: JSON.stringify({
        patient_name: patientName,
        goal_name: goalName,
        target_value: targetValue,
        unit,
      }),
    });
  },
  updateGoal: async (goalId, targetValue, unit = "") => {
    return request(`/health-goals/${goalId}`, {
      method: "PUT",
      body: JSON.stringify({ target_value: targetValue, unit }),
    });
  },
};

// Analytics & Reports API
export const analyticsAPI = {
  getAnalytics: async (limit = 20) => {
    return request(`/health-analytics?limit=${limit}`, { method: "GET" });
  },
  getJourney: async (patientName, limit = 10) => {
    return request(`/health-journey?patient_name=${encodeURIComponent(patientName)}&limit=${limit}`, {
      method: "GET",
    });
  },
  getRiskSummary: async (limit = 20) => {
    return request(`/analytics/risk-summary?limit=${limit}`, { method: "GET" });
  },
  getVitalsChart: async (limit = 20) => {
    return request(`/analytics/vitals-chart?limit=${limit}`, { method: "GET" });
  },
  getHealthReport: async (patientName, params = {}) => {
    const queryParams = new URLSearchParams({
      patient_name: patientName,
      bmi: params.bmi || "",
      steps: params.steps || 0,
      sleep_hours: params.sleep_hours || 0,
      weight_loss_progress_kg: params.weight_loss_progress_kg || 0,
      calorie_intake: params.calorie_intake || 0,
      medications: params.medications || "",
      output_format: params.output_format || "json",
    });
    return request(`/health-report?${queryParams.toString()}`, { method: "GET" });
  },
};

// Chatbot AI API
export const chatbotAPI = {
  chat: async (payload) => {
    return request("/ai-health-chat", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  getConversations: async (limit = 20) => {
    return request(`/conversations?limit=${limit}`, { method: "GET" });
  },
  getMessages: async (conversationId) => {
    return request(`/conversations/${conversationId}/messages`, { method: "GET" });
  },
  submitFeedback: async (messageId, rating, comment = null) => {
    return request("/ai-health-chat/feedback", {
      method: "POST",
      body: JSON.stringify({
        message_id: messageId,
        rating,
        comment,
      }),
    });
  },
};

// Audit Logs API (Restricted to Doctors/Admins)
export const auditAPI = {
  getLogs: async (limit = 100, offset = 0) => {
    return request(`/audit-logs?limit=${limit}&offset=${offset}`, { method: "GET" });
  },
};

// Medications API
export const medicationsAPI = {
  getSchedules: async (patientName) => {
    return request(`/medication-schedule?patient_name=${encodeURIComponent(patientName)}`, {
      method: "GET",
    });
  },
  createSchedule: async (scheduleData) => {
    return request("/medication-schedule", {
      method: "POST",
      body: JSON.stringify(scheduleData),
    });
  },
  getAdherence: async (patientName) => {
    return request(`/medication-adherence?patient_name=${encodeURIComponent(patientName)}`, {
      method: "GET",
    });
  },
  logAdherence: async (adherenceData) => {
    return request("/medication-adherence", {
      method: "POST",
      body: JSON.stringify(adherenceData),
    });
  },
};
