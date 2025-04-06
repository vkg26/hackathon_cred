# 🗣️ VAANI MVP – Voice Assistant for App Navigation and Interaction

## 🚀 Overview

**VAANI (Voice-Assisted AI for Navigation and Interaction)** is a prototype for a generalized voice assistant that helps users—especially those from tier 2–3 cities and elderly users—interact with any Android application through voice commands in regional languages. This MVP focuses on the **core backend logic** and simulates app navigation without relying on the Android layer.

### 🎯 MVP Goal

The goal of this MVP is to:
- Accept a **regional voice input**.
- Convert it to **text using GPT-4o real-time speech-to-text via `litellm`**.
- Match the query with **past similar tasks** using **RAG (Retrieval-Augmented Generation)**.
- Extract **step-by-step instructions** and **corresponding screenshots** from past user actions.
- Loop through the matched steps and simulate a guided walkthrough using hardcoded images.

---

## 🧠 Architecture & Flow

1. **Voice Input (.wav)**
2. **Speech-to-Text** → via `litellm` + GPT-4o real-time - https://docs.litellm.ai/docs/audio_transcription
3. **Query Embedding** → Generate using OpenAI `text-embedding-ada-002`
4. **Similarity Search (RAG)** → Match against past query dataset using FAISS
5. **Retrieve Matching Steps + Images**
6. **Loop through steps** → Show action description + screenshot
7. **Simulated “Next Step”** until task completion

---

## 🛠️ Tech Stack

| Component | Tool/Library |
|----------|---------------|
| Speech-to-Text | [`litellm`](https://github.com/BerriAI/litellm) with GPT-4o real-time |
| Embeddings | OpenAI Ada (`text-embedding-ada-002`) |
| Vector Search | FAISS (or in-memory cosine similarity) |
| Language Model | OpenAI GPT-4o for response formatting |
| Voice File Format | `.wav` (mono, 16kHz recommended) |
| Visualization | CLI or basic web UI (optional for demo) |
| Images | Hardcoded screenshots stored per task |

---

## 📁 Project Structure

