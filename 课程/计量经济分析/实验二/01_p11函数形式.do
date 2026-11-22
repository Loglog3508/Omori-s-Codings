* ============================================================
* 计量经济分析 实验二（第一部分）
* 对应教材 4.1 节「函数形式的确定」（文档第 11 页）
*   4.1.1 对数—线性模型：   y  ->  ln y      （式 4.2—4.7）
*   4.1.2 线性—对数模型：   x  ->  ln x      （式 4.9—4.11）
*   4.1.3 双对数模型：      x,y -> ln x,ln y （式 4.12—4.14）
*   4.1.4 多项式模型：      x 与 x^2         （式 4.15—4.16）
* 数据：演示数据\wage_chap4.dta（14,757 位流动人口）
* 运行：StataMP-64.exe -e do 01_p11函数形式.do
* ============================================================

clear all
set more off
set linesize 132

* ---------- 0. 载入数据并记录日志 ----------
use "..\演示数据\wage_chap4.dta", clear
* wage_chap4.dta 只提供工资的对数 lnwage，这里还原出工资水平（单位：元）
gen wage = exp(lnwage)
label variable wage "月工资（元）"
log using "实验二_第11页.log", replace text

* ============================================================
* 表 A1  函数形式的候选：被解释变量与解释变量
* ============================================================
describe wage lnwage educ exp exp2 lnpop male marr
summarize wage lnwage educ exp exp2 lnpop male marr

* ============================================================
* 一、对数—线性模型（4.1.1 节）
*   模型 wage = b0 + b1*educ + e        （式 4.1）
*   lnwage  = b0 + b1*educ + e          （式 4.7）
*   b1 = dlnY/dX（半弹性），精确百分比变化 100*(exp(b1)-1)（式 4.6）
* ============================================================
* (1) 线性—线性：工资水平对受教育年限
reg wage educ

* (2) 对数—线性：对数工资对受教育年限
reg lnwage educ
display as text "半弹性 b1 = " %7.4f _b[educ] ///
    "，近似百分比变化 = " %6.2f 100*_b[educ] "%" ///
    "，精确百分比变化 = " %6.2f 100*(exp(_b[educ])-1) "%"
* 式（4.2）～（4.5）：ln Y 对 X 的斜率就是半弹性，系数乘 100 即近似百分比
* 式（4.6）：精确百分比变化 = 100*(exp(b1)-1)

* ============================================================
* 二、线性—对数模型（4.1.2 节）
*   Y = b0 + b1*lnX + e                  （式 4.9）
*   b1 = dY/dlnX，X 变动 1% 时 Y 变动 0.01*b1（式 4.11）
* ============================================================
* (3) 工资水平对城市人口规模的对数 — 标准线性—对数形式
reg wage lnpop
display as text "lnpop 增加 1% 时月工资变动 " %7.3f 0.01*_b[lnpop] " 元"
* 式（4.10）：b1 = dY/dlnX = (dY/dX)/(1/X)
* 式（4.11）：dY ≈ b1*(dX/X)，即 X 变动 1% 时 Y 变动 0.01*b1

* (4) 对照：对数工资对 ln(城市人口) —— 这是下一节的双对数形式
reg lnwage lnpop

* ============================================================
* 三、双对数模型（4.1.3 节）
*   lnY = b0 + b1*lnX + e                （式 4.12）
*   b1 = dlnY/dlnX，即弹性                 （式 4.13）
* ============================================================
* (5) 对数工资对城市人口对数：b1 即城市规模的工资弹性
reg lnwage lnpop
display as text "城市规模弹性 b1 = " %7.4f _b[lnpop] ///
    "，城市人口增加 1% 工资增加 " %6.3f _b[lnpop] "%"

* (6) 作为 4.1.1 与 4.1.3 的对照：教育变量的两种写法
reg lnwage educ
reg lnwage lnpop educ

* ============================================================
* 四、多项式模型（4.1.4 节）
*   Y = b0 + b1*X + b2*X^2 + e            （式 4.15）
*   dY/dX = b1 + 2*b2*X，转折点 X* = -b1/(2*b2)（式 4.16）
* ============================================================
* (7) 对数工资对工作经验及其平方（wage_chap4.dta 中已有 exp、exp2）
reg lnwage exp exp2
display as text "工资—经验曲线的转折点 = " %6.2f ///
    -_b[exp]/(2*_b[exp2]) " 年"
* 式（4.16）：b1 + 2*b2*X = 0  =>  X* = -b1/(2*b2)

* (8) 平方项的必要性：与线性设定对比，并检验 H0: b2 = 0
reg lnwage exp
estimates store m_lin
reg lnwage exp exp2
estimates store m_quad
test exp2
estimates restore m_lin
* 用 nestreg 做嵌套模型的 F 检验
nestreg: reg lnwage (exp) (exp2)

* ============================================================
* 五、四种函数形式的比较（R2 与信息准则）
* ============================================================
* 只放城市规模：线性—线性 vs 线性—对数 vs 双对数
reg wage   lnpop
estat ic
reg lnwage lnpop
estat ic

* R2 汇总（逐个回归后用 return list 取值）
reg wage   educ
local r2_1 = e(r2)
reg wage   lnpop
local r2_2 = e(r2)
reg lnwage educ
local r2_3 = e(r2)
reg lnwage lnpop
local r2_4 = e(r2)
reg lnwage exp exp2
local r2_5 = e(r2)
display as text "R2 汇总：wage=educ "   %5.3f `r2_1' ///
    "  wage=lnpop "   %5.3f `r2_2' ///
    "  lnwage=educ "  %5.3f `r2_3' ///
    "  lnwage=lnpop " %5.3f `r2_4' ///
    "  lnwage=exp+exp2 " %5.3f `r2_5'

log close
exit
