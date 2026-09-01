import re

print("\n" + "="*50)
print("4. re.compile 标志参数")
print("="*50)

pattern = re.compile(r'hello', re.I)
print("re.I:", pattern.findall('Hello HELLO hello'))

text = 'first line\nsecond line'
pattern = re.compile(r'^second', re.M)
print("re.M:", pattern.findall(text))

text = 'hello\nworld'
pattern = re.compile(r'hello.world', re.S)
print("re.S:", pattern.findall(text))

text = 'abc 123 你好'
pattern = re.compile(r'\w+', re.U)
print("re.U:", pattern.findall(text))

pattern = re.compile(r"""
    \d{4}   
    -?      
    \d{2}   
    -?     
    \d{2} 
""", re.X)
print("re.X:", pattern.findall('2025-03-07, 2025/03/07, 20250307'))