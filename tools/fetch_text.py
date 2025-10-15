import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import os

def load_source(path_or_url: str) -> str:
    if path_or_url.startswith("http"):
        print("🌍 Fetching article...")
        res = requests.get(path_or_url)
        soup = BeautifulSoup(res.text, "html.parser")
        paragraphs = [p.get_text() for p in soup.find_all("p")]
        return "\n".join(paragraphs)

    elif path_or_url.endswith(".pdf"):
        print("📄 Reading PDF...")
        reader = PdfReader(path_or_url)
        text = "".join(page.extract_text() for page in reader.pages)
        return text

    elif os.path.exists(path_or_url):
        print("📂 Reading local file...")
        with open(path_or_url, "r") as f:
            return f.read()

    else:
        raise ValueError("Unsupported input format.")
