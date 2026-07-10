import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: API_URL,
  timeout: 120000, // 2 minutes (model inference can be slow on first call)
  headers: {
    "Content-Type": "application/json",
  },
});

// Response interceptor for consistent error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.error ||
      error.message ||
      "An unexpected error occurred";
    return Promise.reject(new Error(message));
  }
);

export const api = {
  /**
   * Upload a resume file (PDF or TXT)
   * @param {File} file
   * @returns {Promise<{extracted_text: string, word_count: number, page_count: number}>}
   */
  uploadResume: async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await client.post("/upload-resume", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },

  /**
   * Run full analysis
   * @param {string} resumeText
   * @param {string} jobDescription
   * @returns {Promise<AnalyzeResponse>}
   */
  analyze: async (resumeText, jobDescription) => {
    const response = await client.post("/analyze", {
      resume_text: resumeText,
      job_description: jobDescription,
    });
    return response.data;
  },

  /**
   * Quick match scoring
   * @param {string} resumeText
   * @param {string} jobDescription
   * @returns {Promise<MatchResponse>}
   */
  match: async (resumeText, jobDescription) => {
    const response = await client.post("/match", {
      resume_text: resumeText,
      job_description: jobDescription,
    });
    return response.data;
  },

  /**
   * Health check
   */
  health: async () => {
    const response = await client.get("/health");
    return response.data;
  },
};

export default client;
