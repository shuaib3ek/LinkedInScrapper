import streamlit as st
import requests
import re
import time
import pandas as pd

# -----------------------------
# Utility functions
# -----------------------------

def extract_emails(text):
    return re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)

def extract_phones(text):
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

# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(page_title="LinkedIn Deep Scanner", layout="wide")

st.title("🔍 LinkedIn Profile Deep Scanner (India)")

api_key = st.text_input("Google API Key")
cx = st.text_input("Custom Search Engine ID")
search_name = st.text_input("Search Name / Keywords")
max_pages = st.slider("Max Pages", 1, 10, 3)

if st.button("Search LinkedIn"):
    if not api_key or not cx or not search_name:
        st.warning("Please fill in all fields before searching.")
    else:
        all_results = []
        query = f'{search_name} site:linkedin.com/in India'
        start_index = 1

        for page in range(max_pages):
            data = google_search(api_key, cx, query, start_index)
            if not data or "items" not in data:
                break

            for item in data["items"]:
                title = item.get("title", "")
                link = item.get("link", "")
                snippet = item.get("snippet", "")

                # Deep scan emails & phones from snippet
                emails = extract_emails(snippet)
                phones = extract_phones(snippet)

                all_results.append({
                    "Name": title,
                    "Profile URL": link,
                    "Snippet": snippet,
                    "Emails Found": ", ".join(emails) if emails else "",
                    "Phones Found": ", ".join(phones) if phones else ""
                })

            start_index += 10
            time.sleep(5)  # Delay between pages

        if all_results:
            df = pd.DataFrame(all_results)
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "linkedin_results.csv", "text/csv")
        else:
            st.info("No results found.")