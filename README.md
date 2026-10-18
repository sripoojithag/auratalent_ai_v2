# AuraTalent AI — Intelligent Resume Screening & Candidate Ranking

**An AI-powered recruitment platform that helps identify and rank candidates based on job requirements using semantic search, vector retrieval, and machine learning.**

## Overview

AuraTalent AI is a recruitment assistance platform designed to streamline resume screening and candidate discovery. It processes resumes, extracts structured candidate information, creates vector embeddings, and retrieves and ranks candidates according to a given job description.

The backend combines semantic retrieval, PostgreSQL full-text search, vector similarity, and candidate reranking. It also provides evaluation metrics to assess ranking quality when relevance judgments are available.

## Key Features

- **Resume ingestion:** Extract text from PDF resumes and divide it into manageable chunks.
- **Structured information extraction:** Use an LLM to extract relevant information from resumes.
- **Vector embeddings:** Represent resume content as numerical vectors for semantic search.
- **Hybrid retrieval:** Combine keyword-based retrieval with vector similarity search.
- **Candidate ranking:** Retrieve and rerank candidates based on job requirements.
- **Grounded explanations:** Generate candidate-matching explanations using available evidence.
- **Evaluation metrics:** Calculate Precision@K, Recall@K, Mean Reciprocal Rank (MRR), and Normalized Discounted Cumulative Gain (NDCG@K).
- **REST API:** Expose backend functionality through FastAPI endpoints.
- **Web interface:** Provide a React-based interface for interacting with the platform.

## System Architecture

```text
                  React Frontend
                        |
                        v
                 Node.js Gateway
                        |
                        v
                  FastAPI Backend
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
     PDF Parsing   Embedding       Ranking &
     & Chunking    Service         Retrieval
          |             |             |
          +-------------+-------------+
                        |
                        v
              PostgreSQL + pgvector
                        |
                        v
              Candidate Results
                        |
                        v
              Grounded Explanations
                        |
                        v
               Evaluation Metrics
```

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend API | Python, FastAPI |
| Gateway | Node.js |
| Database | PostgreSQL |
| Vector search | pgvector |
| Embeddings | Google Gemini Embeddings |
| LLM integration | Google Gemini |
| Resume processing | PDF text extraction and chunking |
| Semantic reranking | Cross-Encoder |
| Testing | Pytest |

## How It Works

### 1. Resume Ingestion
PDF resumes are processed to extract text. The extracted content is divided into chunks, and structured candidate information is generated.

### 2. Embedding Generation
Resume chunks are converted into vector embeddings that represent their semantic content. These vectors are stored in PostgreSQL using pgvector.

### 3. Hybrid Candidate Retrieval
Given a job description, the system retrieves potentially relevant candidates using vector similarity and keyword-based search.

### 4. Candidate Reranking
A Cross-Encoder reranks retrieved candidates to improve the ordering of results based on the job description and candidate information.

### 5. Grounded Explanations
The system generates explanations for candidate matches using available candidate and job-related evidence.

### 6. Ranking Evaluation
The evaluation module calculates ranking metrics from ranked candidate IDs and supplied relevance judgments. Reliable real-world evaluation requires an independently established relevance dataset.

## Evaluation Metrics

AuraTalent AI supports the following metrics:

- **Precision@K:** Fraction of the top K retrieved candidates judged relevant.
- **Recall@K:** Fraction of all relevant candidates in the evaluation set retrieved within the top K.
- **MRR:** Measures how highly the first relevant result is ranked.
- **NDCG@K:** Measures ranking quality while accounting for the positions and graded relevance of candidates.

These metrics depend on the relevance judgments supplied to the evaluation process. Metric implementation tests alone do not establish real-world recruitment accuracy.

## Project Structure

```text
auratalent_updated/
├── backend/
│   ├── routers/
│   ├── services/
│   ├── evaluation/
│   ├── tests/
│   ├── config.py
│   └── main.py
├── src/
│   └── App.tsx
├── public/
├── server.ts
├── package.json
├── .gitignore
└── README.md
```

*The structure above highlights the main application areas; individual filenames and directories may vary in your current checkout.*

## Getting Started

### Prerequisites

- Python and a project virtual environment
- Node.js and npm
- PostgreSQL with the pgvector extension
- Required Google Gemini API credentials, if using Gemini-powered functionality

### 1. Clone the repository

```bash
git clone https://github.com/sripoojithag/auratalent_ai_v2.git
cd auratalent_ai_v2
```

### 2. Set up the Python environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the backend dependencies using the project's dependency file and setup instructions.

### 3. Configure environment variables

Create a local `.env` file containing the configuration required by the backend, including database connection settings and Gemini credentials where applicable.

**Never commit API keys, database passwords, or other secrets to GitHub.**

### 4. Install frontend dependencies

```bash
npm install
```

### 5. Start the application

Use the project's configured development command:

```bash
npm run dev
```

The development gateway has previously been configured to serve the frontend and start the FastAPI backend. Ensure PostgreSQL and the required environment variables are configured before using database-dependent features.

## Running Tests

Run the backend test suite from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/ -v
```

To check the installed Pytest version:

```powershell
.\.venv\Scripts\python.exe -m pytest --version
```

Tests cover implemented API functionality and evaluation behaviour. Integration tests may require a reachable database and valid configuration.

## API Capabilities

The backend has included endpoints for functionality such as:

| Endpoint | Purpose |
|---|---|
| `GET /api/status` | Application and database status |
| `GET /api/embeddings/health` | Embedding service health |
| `POST /api/resumes/upload` | Resume ingestion |
| `GET /api/candidates` | Retrieve candidate records |
| `POST /api/init-model` | Initialize ranking resources |
| `POST /api/rank` | Rank candidates against a job description |
| `POST /api/explain` | Generate candidate-match explanations |
| `POST /api/evaluation/run` | Calculate ranking evaluation metrics |

Check the current FastAPI router definitions for the exact request schemas and availability of each endpoint.

Interactive API documentation, when enabled, is available at `/docs` on the FastAPI server.

## Current Limitations

- Ranking quality depends on the completeness and quality of resume data.
- Semantic similarity does not, by itself, prove that a candidate is suitable for a job.
- Meaningful Precision@K and Recall@K evaluation requires trustworthy relevance labels.
- Generated explanations should be checked against the underlying candidate evidence.
- Database availability and API credentials are required for their corresponding integration features.

## Future Improvements

- Build a recruiter-validated benchmark dataset.
- Evaluate retrieval and reranking using repeatable experiments.
- Add richer candidate filters and explainable matching evidence.
- Improve monitoring, error handling, and integration test coverage.
- Introduce access controls and safeguards for sensitive candidate information.

## Responsible Use

AuraTalent AI is intended to assist recruitment workflows, not replace human judgment. Candidate rankings should be reviewed for accuracy, relevance, and potential bias before being used in employment decisions.



GitHub: [@sripoojithag](https://github.com/sripoojithag)

---

*AuraTalent AI — Making candidate discovery more efficient through semantic search and intelligent ranking.*