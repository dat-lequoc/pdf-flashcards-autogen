// ng Window Attention, we have significantly reduced computational overhead while

const FLASHCARD_PROMPT = `Generate flashcards as a JSON array where each object has "question" and "answer" keys. The number of flashcards should be proportional to the text's length and complexity, with a minimum of 1 and a maximum of 10. Each question should test a key concept and the answer should be brief but complete. Use <b> tags to emphasize important words or phrases. Cite short code or examples if needed.

Example input: "In parallel computing, load balancing refers to the practice of distributing computational work evenly across multiple processing units. This is crucial for maximizing efficiency and minimizing idle time. Dynamic load balancing adjusts the distribution of work during runtime, while static load balancing determines the distribution before execution begins."

Example output:
[
  {
    "question": "What is the primary goal of <b>load balancing</b> in parallel computing?",
    "answer": "To <b>distribute work evenly</b> across processing units, maximizing efficiency and minimizing idle time."
  },
  {
    "question": "How does <b>dynamic load balancing</b> differ from <b>static load balancing</b>?",
    "answer": "Dynamic balancing <b>adjusts work distribution during runtime</b>, while static balancing <b>determines distribution before execution</b>."
  }
]

Please output only the JSON array with no additional text or commentary.
Now generate flashcards for the text below:`;

const EXPLAIN_PROMPT = `Explain the following text in simple terms, focusing on the main concepts and their relationships. Use clear and concise language, and break down complex ideas into easily understandable parts. If there are any technical terms, provide brief explanations for them. Return your explanation in a JSON object with an "explanation" key.

Example output:
{
  "explanation": "Load balancing is a technique in parallel computing that ensures work is distributed evenly across different processing units. Think of it like distributing tasks among team members - when done well, everyone has a fair amount of work and the team is more efficient. There are two main approaches: dynamic balancing (adjusting work distribution as needed) and static balancing (planning the distribution ahead of time)."
}

Now explain this text:
Please output only the JSON object with no additional text or commentary.`;

const LANGUAGE_PROMPT = `Return a JSON object with "word", "translation", "question", and "answer" keys for the given word in {targetLanguage}.

Example input:
Word: "refused"
Phrase: "Hamas refused to join a new round of peace negotiations."

Example output:
{
  "word": "refused",
  "translation": "từ chối",
  "question": "Hamas <b>refused</b> to join a new round of peace negotiations.",
  "answer": "Declined to accept or comply with a request or proposal."
}

Sometimes the input may be malformed or incomplete:
Word: "@foreignminister"
Phrase: ""

Example output for malformed input:
{
  "word": "foreign minister",
  "translation": "bộ trưởng ngoại giao",
  "question": "The <b>foreign minister</b> announced new trade agreements with neighboring countries.",
  "answer": "The government minister responsible for a country's foreign policy and relations."
}

Example input for incomplete phrase:
Word: "computational overhead"
Phrase: "ng Window Attention, we have significantly reduced computational overhead while"

Example output:
{
  "word": "computational overhead",
  "translation": "chi phí tính toán",
  "question": "Using Sliding Window Attention, we have significantly reduced <b>computational overhead</b> while maintaining model accuracy.",
  "answer": "The additional computing resources required to perform an operation or run an algorithm."
}


Now explain the word in the phrase below:
Word: "{word}"
Phrase: "{phrase}"
Please output only the JSON object without any additional text or commentary.`; 
