
# My VISTA API Backend Project
This is the main README for the VISTA API Backend.
It contains code for the Google Cloud build.

----

# ⚙️ VISTA API Backend

The **VISTA API Backend** is the core processing engine of the [Veteran Analytics](https://github.com/MarcArmy2003/veteran-analytics) project. It transforms structured Excel and CSV data into clean, chunked `.txt` files for AI analysis and provides a scalable foundation for RESTful data services.

---

## 🎯 Purpose

- Convert government Excel datasets into structured, machine-readable text
- Generate AI-ready documents for ingestion by Vertex AI and related models
- Sync structured outputs to Google Cloud for cloud-based processing

---

## 🧠 Features

- Modular Python scripts for cleaning, chunking, and formatting
- Docker-compatible architecture for deployment
- Includes OpenAPI YAML spec for potential REST interface
- Designed for integration with cloud workflows (e.g., GCS, Vertex AI)

---

## 📁 Folder Structure

```plaintext
vista-api-backend/
├── app/              # Python modules for conversion, chunking, parsing
├── data/             # Input Excel + transcript folders
├── specs/            # OpenAPI specs, GPT action configs
├── scripts/          # Utilities (e.g., unzip, restructure)
├── docs/             # Usage notes, external API references
├── Dockerfile
├── config.yml
├── openapi_spec.yaml
├── requirements.txt
├── .gitignore
└── README.md

----
