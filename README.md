# AI-Powered Regulatory Compliance Checker for Contracts

An AI-powered web application that analyzes contracts and identifies potential regulatory compliance risks using Large Language Models (LLMs).

The application extracts contract text, analyzes individual clauses, identifies potential compliance concerns, classifies risks, and generates a structured compliance report.

## 🚀 Live Demo

**Live Application:**  
https://ai-powered-regulatory-compliance-checker-for-contracts-tsbd3fc.streamlit.app/

## 📌 Overview

Reviewing contracts manually for regulatory compliance can be time-consuming and error-prone.

This project provides an AI-assisted solution that helps users analyze contracts and identify clauses that may require further compliance review.

The application can:

- Upload contract documents in PDF format
- Extract text from contracts
- Split contract content into manageable sections
- Analyze contract clauses using AI
- Identify potential regulatory compliance risks
- Classify identified risks
- Provide explanations and recommendations
- Generate compliance reports
- Store compliance analysis data in Google Sheets
- Provide compliance alert functionality

> **Disclaimer:** This application is an AI-assisted compliance analysis tool and does not replace professional legal advice.

## ✨ Features

### 📄 Contract Upload

Users can upload contract documents in PDF format through the Streamlit web interface.

### 🤖 AI-Powered Clause Analysis

The application uses the Groq API and a Large Language Model to analyze contract clauses and identify potential compliance concerns.

### ⚖️ Regulatory Compliance Analysis

The system can identify potential concerns related to areas such as:

- GDPR
- HIPAA
- Data privacy
- Sensitive data handling
- Data processing
- Data retention
- Data security
- Third-party data sharing

### 🚦 Risk Assessment

Potential compliance issues are categorized based on their risk level, helping users quickly identify clauses that may require attention.

Risk levels include:

- 🔴 High Risk
- 🟠 Medium Risk
- 🟢 Low Risk

### 📊 Compliance Results

The application provides structured results containing:

- Contract clauses
- Identified risks
- Risk levels
- Regulatory concerns
- Explanations
- Recommended actions

### 📑 PDF Report Generation

Users can generate a structured PDF report containing the compliance analysis and identified risks.

### 📋 Google Sheets Integration

Compliance analysis information can be stored in Google Sheets for tracking and further review.

### 🚨 Compliance Alerts

The application includes a compliance alert feature for notifying users about identified compliance concerns.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Web application framework |
| Groq API | AI-powered contract analysis |
| LangChain | Text processing and LLM workflow |
| PyPDF2 | PDF text extraction |
| ReportLab | PDF report generation |
| Google Sheets API | Compliance data storage |
| gspread | Google Sheets integration |
| Pandas | Data processing |
| NumPy | Numerical processing |
| Matplotlib | Data visualization |
| python-dotenv | Environment configuration |

## 🏗️ System Architecture

```text
                    Contract PDF
                         │
                         ▼
                ┌─────────────────┐
                │   PDF Upload    │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  Text Extraction│
                │     PyPDF2      │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Text Processing │
                │   & Chunking    │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │    Groq LLM     │
                │ Clause Analysis │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Risk Assessment │
                │ & Compliance    │
                │    Analysis     │
                └────────┬────────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │   PDF    │ │  Google  │ │  Alerts  │
        │  Report  │ │  Sheets  │ │          │
        └──────────┘ └──────────┘ └──────────┘


## 🔄 How It Works

1. **Upload Contract** – Upload a contract PDF through the application.
2. **Extract Text** – The application extracts text from the uploaded document.
3. **Analyze Clauses** – Contract clauses are analyzed using the Groq LLM.
4. **Identify Risks** – Potential GDPR, HIPAA, privacy, security, and data-handling risks are identified.
5. **Assess Risk** – Each identified issue is categorized based on its risk level.
6. **Generate Report** – A structured compliance report is generated.
7. **Store Results** – Analysis results can be stored in Google Sheets.

## ⚠️ Disclaimer

This application provides AI-assisted compliance analysis for educational and decision-support purposes. It does not constitute legal advice or replace professional legal review.

## 👩‍💻 Author

**Thanuja Reddi**
