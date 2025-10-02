# Job Scraper Installation Guide

This guide explains how to set up and run the job scraper script using a Python virtual environment (`venv`) and install dependencies from a `requirements.txt` file.

## Prerequisites
- Python 3.6 or higher installed
- Git (optional, for cloning the repository)

## Installation Steps

1. **Clone the Repository (Optional)**  
   If the project is hosted on GitHub, clone it:
   ```bash
   git clone https://github.com/RohitMadhu/WashJobScraper
   cd WashJobScraper
   ```

2. **Create a Virtual Environment**  
   Create and activate a virtual environment to isolate dependencies:
   ```bash
   python -m venv venv
   ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

3. **Install Dependencies**  
   Install the required packages from `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
4. **To Utilize LLM functionality**
   Grab a groq API key and define it in your environment variable. 

5. **Run the Script**  
   With the virtual environment activated, run the script:
   ```bash
   python washpostJob.py
   ```

5. **Deactivate the Virtual Environment**  
   When done, deactivate the virtual environment:
   ```bash
   deactivate
   ```

## Requirements File

The `requirements.txt` file lists the necessary Python packages. Ensure it is present in the project directory.
