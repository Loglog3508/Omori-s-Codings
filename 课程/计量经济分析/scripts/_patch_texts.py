# -*- coding: utf-8 -*-
"""去掉 make_word.py 中对 landscan2017城市总人口.dta 之外的引用（封面数据说明、附录 do 文件）。"""
import io

P = r"C:\Users\omori\Omori-s-Codings\课程\计量经济分析\scripts\make_word.py"
s = io.open(P, encoding="utf-8").read()

s = s.replace('["数据", "2017cmds20%子样本_处理后.dta + landscan2017城市总人口.dta"],',
              '["数据", "CMDS 2017 20% 子样本（2017cmds20%子样本_处理后.dta）"],')
s = s.replace('["样本", f"N = {n:,}（289 个城市）"],',
              '["样本", f"N = {n:,}（289 个城市）"],')
s = s.replace('para("变量说明：lnwage 为月工资的自然对数；lnpop 为 LandScan2017 城市总人口的自然对数（按“省代码+市代码”"\n     "匹配到每个个体）；',
              'para("变量说明：lnwage 为月工资的自然对数；lnpop 为样本自带 LandScan2017 城市总人口的自然对数；')
s = s.replace('"注：数据为 2017 年 CMDS 20% 子样本；educ 即受教育年限；marr 即婚姻虚拟变量；lnpop 由 LandScan2017 城市总人口取对数。"',
              '"注：数据为 2017 年 CMDS 20% 子样本；educ 即受教育年限；marr 即婚姻虚拟变量；lnpop 为 LandScan2017 城市总人口取对数。"')
s = s.replace('code_block(open(os.path.join(B.BASE, "do文件", "chapter4_四表.do"), encoding="utf-8").read(),\n           "A. Stata do 文件（chapter4_四表.do）")',
              'code_block(open(os.path.join(B.BASE, "do文件", "chapter4_四表_cmds.do"), encoding="utf-8").read(),\n           "Stata do 文件（chapter4_四表_cmds.do）")')
s = s.replace('para("以下为 Stata 运行代码（chapter4_四表.do），它完成数据合并、变量构造并输出表一至表四，"',
              'para("以下为 Stata 运行代码（chapter4_四表_cmds.do）。数据只用 2017 年 CMDS 20% 子样本一个文件，"')
s = s.replace('     "需 ssc install estout；装有 reghdfe 时会自动改用 reghdfe 吸收行业与职业固定效应。", after=4)',
              '     "脚本自该样本构造变量并输出表一至表四；需 ssc install estout，装有 reghdfe 时自动改用 reghdfe 吸收行业与职业固定效应。", after=4)',)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")