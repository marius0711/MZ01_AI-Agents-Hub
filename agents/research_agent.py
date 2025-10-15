import json
from tools.fetch_text import load_source
from tools.summarize import summarize_chunks
from tools.extract_flashcards import generate_flashcards

class ResearchAgent:
    def __init__(self, model="gpt-4o-mini"):
        self.model = model

    def run(self, source_path: str):
        print("📥 Loading content...")
        text = load_source(source_path)

        print("✂️ Splitting & summarizing...")
        summaries = summarize_chunks(text, self.model)

        print("🧠 Combining summaries...")
        combined = "\n".join(summaries)

        print("🎓 Generating flashcards...")
        flashcards = generate_flashcards(combined, self.model)

        output = {
            "summary": combined,
            "flashcards": flashcards
        }

        # Save results
        with open("data/output/summary.json", "w") as f:
            json.dump(output, f, indent=2)

        with open("data/output/summary.md", "w") as f:
            f.write("## 🧠 Zusammenfassung\n")
            f.write(combined + "\n\n")
            f.write("## 🎓 Lernkarten\n")
            for fc in flashcards:
                f.write(f"**Frage:** {fc['question']}\n")
                f.write(f"**Antwort:** {fc['answer']}\n\n")

        return output
