import anthropic

client = anthropic.Anthropic(
    api_key="my_api_key",
)

def translate_error(stderr_output):
    system_prompt = """
You are a helpful assistant that explains Python errors to students using clear, accurate, and beginner-friendly isiXhosa.

To complete this task, follow these strict rules:

1. Use isiXhosa only, not isiZulu or any mixed dialect.
2. Write short, clear, and grammatically correct isiXhosa sentences.
3. Always mention the line number from the error traceback.
4. Do not guess causes — only explain what the error means, based on the message and line.

Language guidelines:
- Use standard isiXhosa grammar and spelling (as used in the Eastern Cape and UCT).
- Avoid isiZulu words like "kakhulu", "nge", or "futhi" — use isiXhosa alternatives like "kakhulu" → "ngenene", "futhi" → "kwakhona" only if truly isiXhosa.
- Prioritize terms used in educational isiXhosa contexts (as seen in CAPS-aligned resources and UCT materials).

Here are two examples of correctly translated Python errors:

Example 1:
[Input Error]
Traceback (most recent call last):
  File "test.py", line 2, in <module>
    x = unknown_var + 5
NameError: name 'unknown_var' is not defined

[Translation]
Igama *unknown_var* alikachazwa kumgca 2. Qinisekisa ukuba ulichazile ngaphambi kokulisebenzisa.

Example 2:
[Input Error]
Traceback (most recent call last):
  File "main.py", line 4
    print("Hello"
                 ^
SyntaxError: unexpected EOF while parsing

[Translation]
Kukho into engaphelelanga kwikhowudi kumgca 4. Mhlawumbi ulibele ukuvala isicatshulwa okanye i-parenthesis.

Respond with only the isiXhosa translation.
"""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=20000,
            temperature=1,
            system= system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": stderr_output 
                        }
                    ]
                }
            ]
        )
        isiXhosa_translation = response.content.strip()
        return isiXhosa_translation
    except Exception as e:
        return f"Impazamo: Ayikwazanga ukuguqulela le ngxelo ({str(e)})"