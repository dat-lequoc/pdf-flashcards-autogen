const MODEL_API_KEY_MAPPING = {
  "gemini/gemini-exp-1206": "GEMINI_API_KEY",
//   "gemini/gemini-2.0-flash": "GEMINI_API_KEY",
//   "gemini/gemini-2.0-flash-lite-preview-02-05": "GEMINI_API_KEY",
//   "gemini/gemini-2.0-pro-exp-02-05": "GEMINI_API_KEY",
//   "gemini/gemini-2.0-flash-thinking-exp-01-21": "GEMINI_API_KEY",
  "openrouter/google/gemini-exp-1206:free": "OPENROUTER_API_KEY",
  "openrouter/anthropic/claude-3-haiku-20240307": "OPENROUTER_API_KEY",
  "openrouter/anthropic/claude-3-sonnet-20240229": "OPENROUTER_API_KEY"
};

const availableModels = Object.keys(MODEL_API_KEY_MAPPING);

// Removed MODEL_LABELS as they are no longer needed. 