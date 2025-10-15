from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI

def summarize_chunks(text, model="gpt-4o-mini", chunk_size=3000):
    client = OpenAI()

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=200)
    chunks = splitter.split_text(text)

    summaries = []
    for i, chunk in enumerate(chunks, 1):
        print(f"🪄 Summarizing chunk {i}/{len(chunks)}...")
        prompt = f"Summarize the following text in 5 concise bullet points:\n\n{chunk}"
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        summaries.append(response.choices[0].message.content.strip())

    return summaries
