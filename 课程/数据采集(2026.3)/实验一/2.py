import re
print("\n" + "="*50)
print("2. 预定义元字符示例")
print("="*50)

print("\\d :", re.findall(r'\d+', 'age: 25, price: 99.9'))

print("\\D :", re.findall(r'\D+', 'age: 25, price: 99.9'))

print("\\w :", re.findall(r'\w+', 'hello_world 123'))

print("\\W :", re.findall(r'\W+', 'hello_world 123'))

print("\\s :", re.findall(r'\s+', 'hello world\t123\n'))

print("\\S :", re.findall(r'\S+', 'hello world\t123\n'))

print("\\b :", re.findall(r'\bcat\b', 'cat category copycat'))

print("\\B :", re.findall(r'\Bcat\B', 'category'))

print(".  :", re.findall(r'c.t', 'cat cut c#t c\nt'))