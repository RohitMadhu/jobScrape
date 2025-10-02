from requests_html import HTMLSession
import re
import json
import time
from requests.exceptions import RequestException
from groq import Groq
import os

session = HTMLSession()
url = "https://classifiedsmarketplace.washingtonpost.com/marketplace/search/query?categoryId=154" \
"&searchProfile=recruitment&source=&page=1&size=1000&view=list&showExtended=false&startRange=&keywords=" \
"&minSalary=&maxSalary=&location=&postCode=&searchRadius=&searchUnit=MILES&ordering="

# Fetch job listing URLs
try:
    r = session.get(url, timeout=10)
    jobs = {i for i in r.html.links if "https://classifiedsmarketplace.washingtonpost.com/marketplace//advert/" in i}
except RequestException as e:
    print(f"Error fetching main page: {e}")
    jobs = set()

# Collect job content and URLs with retry and delay
jobsData = []
for job_url in jobs:
    for attempt in range(3):  # Retry up to 3 times
        try:
            response = session.get(job_url, timeout=10)
            content = response.html.find('div.sr_ad_content.panel.panel-details', first=True)
            if content:
                jobsData.append((content.text, job_url))
            break
        except RequestException as e:
            print(f"Error fetching {job_url}, attempt {attempt + 1}: {e}")
            if attempt == 2:
                print(f"Failed to fetch {job_url} after 3 attempts")
            time.sleep(1)  # Delay between retries
    time.sleep(0.5)  # Delay between requests to avoid overwhelming server

# Regex patterns for job details
patterns = {
    "title": r'^(.*?)(?=\n|$)',  # First line is the title
    "description": r'\n(.*?)(?=\n• Company Name)',  # Text between title and company name
    "company": r'• Company Name - (.*?)(?=\n|$)',  # Company name
    "industry": r'• Job Industry - (.*?)(?=\n|$)',  # Industry (first occurrence)
    "status": r'• Job Status - (.*?)(?=\n|$)',  # Job status
    "city": r'• City - (.*?)(?=\n|$)',  # City
    "zip": r'• Zip - (.*?)(?=\n|$)',  # Zip code
    "location": r'location\n(.*?)(?=\n|$)',  # Location
    "post_date": r'Post Date: (\d{2}/\d{2})',  # Post date (MM/DD)
    "refcode": r'Refcode: #?([C0-9]+)'  # Refcode
}

# Regex patterns for PERM identification
perm_patterns = {
    "physical_address": r'(?:Send resume to|Mail (?:resume|CV|res)).*?\d{5}',  # Physical address with zip
    "email_to_person": r'(?:Email|mail).*?@.*?\.(?:com|org|edu)\b'  # Email to a person
}

# Function to determine PERM status
def get_perm_status(description):
    has_physical_address = re.search(perm_patterns["physical_address"], description, re.IGNORECASE)
    has_email_to_person = re.search(perm_patterns["email_to_person"], description, re.IGNORECASE)
    has_visa_sponsorship = re.search(r'visa\s*sponsor', description, re.IGNORECASE)
    has_apply_link = re.search(r'Link to apply:.*?https?://', description, re.IGNORECASE)

    if has_physical_address:
        return "likely" if has_visa_sponsorship else "possible"
    if has_email_to_person and not has_apply_link:
        return "maybe" if has_visa_sponsorship else "maybe"
    return "unlikely"

# Function to determine PERM status with LLM
def get_perm_status_llm(description):
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": f"You are an expert in US immigration law, specifically PERM (Program Electronic Review Management) labor certification ads. Analyze: {description}. Output only: 'Yes' if PERM ad; 'No' otherwise."
                }
            ],
            temperature=0.1,
            max_tokens=10,
            stream=False
        )
        response = completion.choices[0].message.content.strip()
        return "Yes" if "Yes" in response else "No"
    except Exception as e:
        print(f"LLM error: {e}")
        return "Error"

# Function to parse job listing
def parse_job(job_data):
    content, job_url = job_data  # Unpack tuple of content and URL
    job = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, content, re.DOTALL)
        if match:
            job[key] = match.group(1).strip()
    job["url"] = job_url
    job["perm_status"] = get_perm_status(job.get("description", ""))
    job["perm_status_ai"] = get_perm_status_llm(job.get("description", ""))
    return job

# Parse all job listings and save partial results
job_listings = []
for job in jobsData:
    try:
        job_listings.append(parse_job(job))
        # Save partial results every 10 jobs
        if len(job_listings) % 10 == 0:
            with open('job_listings_partial.json', 'w') as f:
                json.dump({"jobs": job_listings}, f, indent=4)
    except Exception as e:
        print(f"Error parsing job {job[1]}: {e}")

# Save final results
try:
    with open('job_listings.json', 'w') as f:
        json.dump({"jobs": job_listings}, f, indent=4)
    print("Job listings saved to job_listings.json")
except Exception as e:
    print(f"Error saving final JSON: {e}")