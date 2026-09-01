import re

print("="*50)
print("1. 元字符示例")
print("="*50)

print("^ :", re.findall(r'^Hello', 'Hello World')) 
print("$ :", re.findall(r'World$', 'Hello World')) 

print("* :", re.findall(r'ab*', 'a ab abb abbb'))
print("+ :", re.findall(r'ab+', 'a ab abb abbb'))

print("? :", re.findall(r'ab?', 'a ab abb abbb'))

print("{}:", re.findall(r'ab{2}', 'a ab abb abbb'))
print("{}:", re.findall(r'ab{2,3}', 'a ab abb abbb'))

print("[]:", re.findall(r'[aeiou]', 'hello world'))

print("\\ :", re.findall(r'\.', 'www.example.com'))

print("| :", re.findall(r'cat|dog', 'I have a cat and a dog'))

match = re.search(r'(\d{4})-(\d{2})-(\d{2})', '2025-03-07')
print("():", match.groups())