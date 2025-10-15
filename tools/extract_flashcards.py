from openai import OpenAI

def generate_flashcards(text, model="gpt-4o-mini"):
    client = OpenAI()

    prompt = (
        "Create 5 flashcards (question-answer pairs) from the following text. "
        "Return as JSON list with keys 'question' and 'answer'.\n\n"
        f"{text}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    import json
    try:
        cards = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        cards = [{"question": "Error", "answer": "Failed to parse output"}]

    return cards
