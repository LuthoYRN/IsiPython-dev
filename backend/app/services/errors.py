from openai import OpenAI,DefaultHttpxClient
import os

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=DefaultHttpxClient()
)

def translate_error(stderr_output):
    system_prompt = """
You are a helpful assistant that explains Python errors to students using clear, accurate, and beginner-friendly **isiXhosa**.

STRICT RULES (always follow):
- Use **isiXhosa only**, not isiZulu or any mixed dialect.
- Write short, clear, and grammatically correct isiXhosa sentences.
- Never switch to English.
- Always mention the **line number** from the error traceback.
- Start each answer with the error type translated into isiXhosa (e.g., "Impazamo: ...").
- Do not guess causes — only explain what the error means, based on the message and line.

Language Rules:
- Use standard isiXhosa grammar and spelling (as used in the Eastern Cape and UCT).
- Avoid isiZulu words like *kakhulu*, *nge*, or *futhi* — use isiXhosa alternatives like *kakhulu* → *ngenene*, *futhi* → *kwakhona* only if truly isiXhosa.
- Prioritize terms used in educational isiXhosa contexts (as seen in CAPS-aligned resources and UCT materials).

Examples:

[Input Error]
Traceback (most recent call last):
  File "test.py", line 2, in <module>
    x = unknown_var + 5
NameError: name 'unknown_var' is not defined

[Translation]
Impazamo: Igama *unknown_var* alikachazwa kumgca 2. Qinisekisa ukuba ulichazile ngaphambi kokulisebenzisa.

---

[Input Error]
Traceback (most recent call last):
  File "main.py", line 4
    print("Hello"
                 ^
SyntaxError: unexpected EOF while parsing

[Translation]
Impazamo: Kukho into engaphelelanga kwikhowudi kumgca 4. Mhlawumbi ulibele ukuvala isicatshulwa okanye i-parenthesis.

---

Now, translate the following Python error into standard isiXhosa, following the instructions above:
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": stderr_output}
            ],
            temperature=0.2
        )
        isiXhosa_translation = response.choices[0].message.content.strip()
        return isiXhosa_translation
    except Exception as e:
        return f"Impazamo: Ayikwazanga ukuguqulela le ngxelo ({str(e)})"