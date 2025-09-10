# EduVid AI: PDF Notes to Video Summaries

A hackathon project for HackMIT that transforms PDF notes into short, engaging educational videos using AI-generated scripts, voiceovers, and visuals.

---

## 🚀 Getting Started

Follow these instructions to set up and run the backend PDF parsing service on your local machine.

### Prerequisites

* Python 3.8+
* pip (Python package installer)
* Git

### 1. Clone the Repository

First, clone the repository to your local machine:
```bash
git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd your-repo-name


### 2. Create the virtual environment

python -m venv venv

# Activate it (on Windows)
venv\Scripts\activate

# Activate it (on macOS/Linux)
source venv/bin/activate

### 3. Install Dependencies

```bash
pip install -r requirements.txt


### 4. Run the App

```bash
uvicorn parser:app --reload

Go to "http://127.0.0.1:8000/docs"

or

```bash
python test_client.py



