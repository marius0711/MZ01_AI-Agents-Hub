from agents.research_agent import ResearchAgent
from dotenv import load_dotenv
load_dotenv()


def main():
    agent = ResearchAgent(model="gpt-4o-mini")  # oder "claude-3-opus"
    source = input("🔗 Enter URL or path to PDF: ").strip()

    result = agent.run(source)

    print("\n✅ Summary created!")
    print(f"- Markdown: data/output/summary.md")
    print(f"- JSON: data/output/summary.json")

if __name__ == "__main__":
    main()
