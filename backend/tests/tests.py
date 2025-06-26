import requests

code = """ukusuka math ngenisa 
x = 5
y = 10
print(x + y)
"""

response = requests.post(
    "http://localhost:5000/api/code",
    json={"code": code}
)

print(response.json())