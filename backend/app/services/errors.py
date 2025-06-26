from openai import OpenAI,DefaultHttpxClient
import os

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=DefaultHttpxClient()
)

def translate_error(stderr_output):
    system_prompt = f"""
You are a helpful assistant that explains Python errors to students in **beginner-friendly isiXhosa**.

Follow these rules strictly:
- Do NOT explain in English.
- Use simple isiXhosa, short sentences.
- Always begin with the error type in isiXhosa.
- Mention the **line number** where the error happened.
- Do NOT guess the cause — only describe what the error message actually means.

Examples:

[Input Error]
Traceback (most recent call last):
  File "test.py", line 2, in <module>
    x = unknown_var + 5
NameError: name 'unknown_var' is not defined

[Translation]
Impazamo: Igama *unknown_var* alikachazwa kumgca 2. Qinisekisa ukuba uyibhalile into ngaphambili.

---

[Input Error]
Traceback (most recent call last):
  File "main.py", line 4
    print("Hello"
                 ^
SyntaxError: unexpected EOF while parsing

[Translation]
Impazamo: Kukho into engaphelelanga kwikhowudi kumgca 4. Ulibele ukuvala isicatshulwa okanye i-parenthesis.

---
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