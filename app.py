import streamlit as st
import requests
import re
import time
import pandas as pd

# -----------------------------
# Utility functions
# -----------------------------

def extract_emails(text):
    """Extract emails from text"""
    return re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)

def extract_phones(text):
    """Extract phone numbers from text"""
    return re.findall(r"\+?\d[\d\s\-]{7,15}\d", text)

def google_search(api_key, cx, query, start_index):
    """Perform Google Custom Search"""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "start": start_index
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"API Error {response.status_code}: {response.text}")
        return None

def fetch_profile_page(url):
    """Fetch full LinkedIn profile page HTML"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            return ""
    except:
        return ""

def extract_contacts_from_html(html):
    """Extract emails and phones from HTML"""
    emails = extract_emails(html)
    phones = extract_phones(html)
    return ", ".join(emails), ", ".join(phones)

# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(page_title="Trainer Deep Scanner", layout="wide")
st.title("🔍 LinkedIn Past or Present Trainer / Mentor / Consultant Scanner")

api_key = st.text_input("Google API Key")
cx = st.text_input("Custom Search Engine ID")
technology = st.text_input("Main Technology / Skill (e.g., Python, Java, Power BI)")
related_tools = st.text_input("Related Frameworks / Tools (comma-separated, optional)")
location = st.text_input("Location (Optional, e.g., India)")
max_pages = st.slider("Max Pages to Scan", 1, 5, 2)  # reduce pages for profile fetching speed

if st.button("Search Trainers / Mentors / Consultants"):
    if not api_key or not cx or not technology:
        st.warning("Please fill in API Key, CSE ID, and Technology.")
    else:
        all_results = []

        # Prepare technology keywords
        technology_keywords = [technology.strip()]
        if related_tools:
            technology_keywords += [t.strip() for t in related_tools.split(",")]

        # Broader roles for past or present training experience
        training_keywords = [
            "trainer", "instructor", "training", "mentored", "conducted training", "taught",
            "mentor", "consultant", "coach"
        ]

        # Build Google query
        query = f'site:linkedin.com/in ({" OR ".join(technology_keywords)}) ({" OR ".join(training_keywords)})'
        if location:
            query += f' "{location}"'

        st.info(f"Searching for: {query}")
        start_index = 1

        for page in range(max_pages):
            data = google_search(api_key, cx, query, start_index)
            if not data or "items" not in data:
                break

            for item in data["items"]:
                title = item.get("title", "")
                link = item.get("link", "")
                snippet = item.get("snippet", "")

                # Fetch full profile HTML to expand snippet
                html_content = fetch_profile_page(link)
                if not html_content:
                    html_content = snippet  # fallback to snippet if page fetch fails

                snippet_lower = html_content.lower()
                title_lower = title.lower()

                # Include result if it mentions any training role + any tech keyword
                if (any(k.lower() in snippet_lower or k.lower() in title_lower for k in training_keywords) and
                    any(t.lower() in snippet_lower + title_lower for t in technology_keywords)):

                    emails, phones = extract_contacts_from_html(html_content)

                    all_results.append({
                        "Name": title,
                        "Profile URL": link,
                        "Snippet / Full Text": html_content[:500] + "..." if len(html_content) > 500 else html_content,
                        "Emails Found": emails,
                        "Phones Found": phones
                    })

            start_index += 10
            time.sleep(5)  # Delay to avoid Google API rate limits

        if all_results:
            df = pd.DataFrame(all_results)
            st.success(f"Found {len(all_results)} relevant profiles!")
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "trainer_results_full.csv", "text/csv")
        else:
            st.info("No relevant profiles found.")
