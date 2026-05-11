# 🚀 Lead Accelerator

Lead Accelerator is a full-stack lead generation tool designed to automate the process of finding professional email addresses from a list of companies. It leverages the **Hunter.io API** to perform domain searches and stores the results in a **PostgreSQL** database.

---

## ✨ Features

* **File Upload**: Supports both `.csv` and Excel (`.xlsx`, `.xls`) file formats for processing company lists.
* **Automated Email Discovery**: Integrates with the Hunter.io API to fetch emails, confidence scores, and contact names.
* **Intelligent Fallback**: If no emails are found via API or credits are exhausted, the system generates common patterns like `info@`, `contact@`, and `sales@`.
* **Data Persistence**: Every processed lead is saved to a PostgreSQL database with a unique `batch_id` for historical tracking.
* **Domain Filtering**: Automatically filters out generic domains like `gmail.com`, `yahoo.com`, and `hotmail.com` to ensure professional leads.
* **CSV Export**: Allows users to download a structured CSV report of any processed batch.
* **Modern UI**: A dark-themed, responsive dashboard featuring a progress bar and real-time result table.

---

## 🛠️ Tech Stack

* **Frontend**: HTML5, CSS3 (Inter Font), and Vanilla JavaScript.
* **Backend**: FastAPI (Python 3.10).
* **Database**: PostgreSQL with SQLAlchemy ORM.
* **API**: Hunter.io Domain Search & Account API.
* **DevOps**: Docker & Docker Compose.

---

## 📋 Prerequisites

* **Python 3.10+** (if running without Docker).
* **Docker & Docker Compose** (recommended).
* **Hunter.io API Key**: Required to fetch professional emails.

---

## 🚀 Getting Started

### 1. Environment Setup
Create a `.env` file in the root directory and configure your credentials:

```env
# Your Hunter API key
HUNTER_API_KEY = "your_api_key_here"

# Local Docker database URL
DATABASE_URL="postgresql://postgres:password@db:5432/leadgen_db"


---

## 🛠️ Future Enhancements & Roadmap

To transform from a lead extraction tool into a high-conversion **Outreach Engine**, the following modules are currently under development:

### 🤖 1. Local AI Copywriting (Ollama Integration)
Instead of generic templates, use local LLMs to craft hyper-personalized messages.
* **Contextual Drafting**: Integrate with **Ollama** (Llama 3 or Mistral) to analyze a lead's `position` and `company_name` to generate unique subject lines and email bodies.
* **Privacy & Cost**: Processing happens locally on your machine, ensuring data privacy and zero per-message API costs.
* **Multi-Tone Support**: Toggle between professional, casual, or "problem-solver" tones based on the target industry.

### 📧 2. Automated Cold Outreach (SMTP)
Move from downloading CSVs to hitting "Send" directly from the dashboard.
* **Custom SMTP Configuration**: Support for adding multiple sender accounts (Gmail, Outlook, or private SMTP servers).
* **Smart Throttling**: Built-in delays and daily sending limits to protect your domain reputation and stay under provider caps.
* **Email Sequencing**: Set up automated follow-ups if a lead doesn't respond within a specific timeframe.

### 📊 3. Advanced Tracking & Analytics
Gain deep insights into how your leads are interacting with your emails.
* **Seen Rate (Open Tracking)**: Implementation of a transparent 1x1 tracking pixel to monitor when and how many times an email is opened.
* **Click-Through Rate (CTR)**: URL wrapping to track which links (calendly, portfolio, website) the lead clicks on.
* **Bounce & Reply Detection**: Automatically flag "Dead" emails in the database and stop sequences once a lead replies.

### 🗂️ 4. CRM-Style Lead Management
* **Status Tags**: Label leads as `New`, `Contacted`, `Replied`, or `Converted` within the UI.
* **Enriched Profiles**: Automatically pull LinkedIn profiles or company news to provide more "hooks" for the AI writer.

---
