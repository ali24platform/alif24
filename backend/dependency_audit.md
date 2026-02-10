# 📦 Dependency Impact Analysis (Vercel Size Audit)

**Status:** Critical (Over 250MB Limit)
**Goal:** Reduce size by removing non-essential heavy libraries.

## 1. The "Fat" Culprits (Top 3 Candidates)

| Dependency | Purpose | Est. Size (Unzipped) | Verdict |
| :--- | :--- | :--- | :--- |
| **`azure-cognitiveservices-speech`** | Text-to-Speech & Speech-to-Text | **~80MB+** (Contains native binaries) | **CRITICAL** (See Strategy) |
| **`pdfplumber`** | PDF Parsing for TestAI | **~30MB** (Requires `pdfminer.six`, `Pillow`) | **DELETE** (Use `pypdf`) |
| **`pillow`** | Image Processing | **~45MB** | **DELETE** (Move OCR to client or use lightweight alternative) |

## 2. Recommended "Delete" List

These packages provide features that are either:
1.  **Secondary** (Admin/Teacher only tools like creating quizzes from PDF/Image).
2.  **Redundant** (Can be done with lighter libs).
3.  **Broken on Serverless** (`pytesseract` requires system binaries which Vercel doesn't have).

*   `pdfplumber` (Use `pypdf` which is already included)
*   `pillow` (Only used for OCR which needs pytesseract)
*   `pytesseract` (Does not work on standard Vercel runtime anyway)
*   `python-docx` (Admin feature, strictly necessary?)
*   `langdetect` (Keep ~5MB, acceptable)
*   `emails` (Use standard `smtplib` or `email-validator` + `httpx` for APIs)

## 3. The Strategy for Azure Speech (`azure-cognitiveservices-speech`)

This is your heaviest dependency.
*   **Problem:** It includes heavy native C++ libraries.
*   **Solution A (Quick):** Remove it from `requirements.txt`. The code is already refactored to use `try...except ImportError`, so the app **will not crash**. The TTS/STT features will just return errors or mock responses on Vercel.
*   **Solution B (Long Term):** Refactor `router.py` to use **Azure REST API** (`requests.post(...)`) instead of the SDK. This removes the 80MB dependency entirely while keeping the feature working.

## 4. Optimized `requirements.txt` (Proposal)

See the generated file below. I have removed the heavy "TestAI" parsing libraries and commented out `azure-cognitiveservices-speech` for you to try a deployment without it (to see if size drops enough).
