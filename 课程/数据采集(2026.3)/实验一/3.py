import re

print("\n" + "="*50)
print("3. 大连市电话号码匹配")
print("="*50)

pattern = r'^0411-?\d{8}$'
test_numbers = ['0411-01234567', '041101234567', '0411-12345678', '041112345678', '0411-0123456', '0411-012345678']
for num in test_numbers:
    if re.match(pattern, num):
        print(f"匹配成功: {num}")
    else:
        print(f"匹配失败: {num}")