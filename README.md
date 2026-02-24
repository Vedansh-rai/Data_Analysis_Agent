# 📊 Data Analysis Agent

An AI-powered data analysis platform that lets you upload any CSV dataset, chat with it in natural language, generate interactive visualizations, and export Tableau-ready files — all through a clean web interface.

---

## ✨ Features

- **Conversational Analysis** — Ask questions about your data in plain English powered by a local LLM (Ollama / llama3)
- **Auto Visualization** — Automatically generates interactive bar charts and scatter plots using Altair/Vega-Lite
- **Insight Generation** — Statistical summaries, trend detection, and data quality alerts
- **Tableau Export** — One-click export to `.tds` Tableau Data Source files
- **Markdown Reports** — Auto-generated analysis reports saved to `output/reports/`
- **Custom Axis Selection** — Pick your own X/Y axes for targeted chart generation

---

## 🏗️ Architecture

```
Data Analysis Agent
├── backend/
│   ├── main.py                  # FastAPI application & API routes
│   ├── src/
│   │   ├── opal.py              # Core orchestrator (pipeline brain)
│   │   ├── antigravity_core.py  # Data ingestion & statistical analysis
│   │   ├── chart_engine.py      # Vega-Lite chart generation
│   │   ├── llm_client.py        # Ollama LLM client (natural language routing)
│   │   ├── tableau_connector.py # Tableau .tds export
│   │   ├── auto_dashboard.py    # Automated dashboard builder
│   │   └── analyzer.py          # Supplementary analysis utilities
│   └── requirements.txt
├── frontend/                    # Vite + React frontend
│   └── src/
│       ├── App.jsx
│       └── App.css
├── data/
│   └── raw/                     # Uploaded datasets stored here
├── output/
│   ├── charts/                  # Generated HTML/JSON chart files
│   ├── reports/                 # Markdown analysis reports
│   └── tableau/                 # Tableau export files
└── run_app.sh                   # One-command startup script
```

### Pipeline Flow

```
Upload CSV → Antigravity (Ingest & Analyze) → Opal (Orchestrate)
    → LLM Client (NL Routing) → Chart Engine (Visualize)
    → Report Generator → Frontend
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.com/) running locally with `llama3` model

```bash
# Pull the required model
ollama pull llama3
```

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/Vedansh-rai/Data_Analysis_Agent.git
cd Data_Analysis_Agent
```

**2. Install backend dependencies**
```bash
cd backend
pip install -r requirements.txt
```

**3. Install frontend dependencies**
```bash
cd frontend
npm install
```

### Running the App

Use the one-command startup script from the project root:

```bash
chmod +x run_app.sh
./run_app.sh
```

Or start services manually:

```bash
# Terminal 1 — Backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

| Service  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost:5173       |
| Backend  | http://localhost:8000       |
| API Docs | http://localhost:8000/docs  |

---

## 🔌 API Reference

| Method | Endpoint         | Description                              |
|--------|------------------|------------------------------------------|
| `POST` | `/upload`        | Upload a CSV file                        |
| `POST` | `/analyze`       | Run the full analysis pipeline           |
| `POST` | `/chat`          | Conversational query against dataset     |
| `GET`  | `/columns`       | Get column names and types for a file    |
| `POST` | `/export/tableau`| Generate a Tableau `.tds` export file    |

---

## 🛠️ Tech Stack

| Layer     | Technology                        |
|-----------|-----------------------------------|
| Backend   | FastAPI, Uvicorn                  |
| AI / LLM  | Ollama (llama3), OpenAI-compatible|
| Data      | Pandas, NumPy, SciPy              |
| Charts    | Altair (Vega-Lite)                |
| Frontend  | React (Vite)                      |
| Export    | Tableau TDS, XLSX (openpyxl)      |

---

## 📂 Sample Data

Sample datasets are included in `data/raw/` and `backend/data/raw/`:
- `sales_data.csv` — General sales dataset
- `Nike_Sales_Uncleaned.csv` — Nike sales data (with data quality issues for testing)

---

## 📄 License

MIT License. Feel free to fork and build on top of this project.
