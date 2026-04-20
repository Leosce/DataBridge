# DataBridge — Setup & Run Guide

A Chainlit-based AI assistant for querying and editing Excel files using a ReAct agent loop.

---

<img width="1920" height="1080" alt="2026-04-21 00-47-24" src="https://github.com/user-attachments/assets/09081323-171c-4191-8bab-d23dd6e00cca" />

## Prerequisites

- Python 3.9+
- At least one API key from the supported providers below

---

## 1. Clone / Download the Project

Ensure your project folder contains the following structure:

```
DataBridge/
├── main.py
├── app.py
├── .env
├── data_original/
│   ├── Real Estate Listings.xlsx
│   └── Marketing Campaigns.xlsx
└── data_modified/        ← created automatically on first write
```

---

## 2. Install Dependencies

```bash
pip install chainlit pandas pydantic openpyxl groq openai google-genai python-dotenv tabulate
```

---

## 3. Set Up API Keys

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_key_here
NVIDIA_API_KEY=your_nvidia_key_here
GEMINI_API_KEY=your_gemini_key_here
```

You only need keys for the models you want to use. The app defaults to Groq if no selection is made, so at minimum provide `GROQ_API_KEY`.

**Where to get keys:**
- Groq: https://console.groq.com
- NVIDIA: https://integrate.api.nvidia.com
- Gemini: https://aistudio.google.com/app/apikey

---

## 4. Run the App

```bash
chainlit run app.py
```

This opens the app in your browser at `http://localhost:8000`.

---

## 5. Using the App

1. Select a model from the buttons at the start of the session
2. Ask data questions or give instructions in plain English

**Example prompts:**
- `Show me all properties in California with a list price above $500,000`
- `Which marketing channel has the highest average revenue?`
- `Find the 3 worst ROI campaigns and delete them`
- `Add a new property listing in Austin, Texas`
- `List the top 5 list prices and delete them, then add dummy data`

Write operations (add, update, delete) will always show a confirmation preview before executing.

---

## 6. Data Files

- `data_original/` — source files, never modified
- `data_modified/` — all changes are written here; the app always reads from this folder first

To reset to original data, delete the files inside `data_modified/`.

---

## Notes

- Tool calls must use **positional arguments** — this is handled automatically by the model given the system prompt
- The `.chainlit/translations/` folder is not required and can be deleted
- Groq is recommended for best performance due to lower latency per ReAct turn
