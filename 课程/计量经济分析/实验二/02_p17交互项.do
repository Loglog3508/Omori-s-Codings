* ============================================================
* 计量经济分析 实验二
* 教材《回归模型的进一步议题》第 17 页：
*   题 1 → 4.3.2 虚拟变量和定量变量的交互（式 4.23—4.28）
*            + 4.3.3 定量和定量变量的交互（式 4.29—4.33）
*   题 2 → 4.5 Stata 应用（式 4.37A / 4.37B，reghdfe + margins + center）
* 数据：..\演示数据\wage_chap4.dta（14,757 位流动人口；变量名与
*       CMDS2017sample 相同，均与教材一致）
* 环境：4.37A/4.37B 需要 ftools、reghdfe、center 三个第三方命令。
*       本机 SSC 站点无法写入 C:\Users\omori\ado\plus，故已把它们
*       下载到 ..\ado_work 并用 adopath 挂载；如果你的电脑已经
*       ssc install ftools / reghdfe / center，可删掉 adopath 一行。
* 运行：StataMP-64.exe -e do 02_p17交互项.do
* ============================================================

clear all
set more off
set linesize 132
* 第三方命令目录（reghdfe 需要 ftools、require、moremata）
adopath ++ "..\ado_work"

use "..\演示数据\wage_chap4.dta", clear
log using "实验二_第17页.log", replace text

* ============================================================
* 表 1  样本描述
* ============================================================
summarize lnwage lnpop educ male marr exp exp2 age city_time health
tabulate health
tabulate hangye
tabulate zhiye
display as text "educ 均值 = " %8.4f r(mean)   // 供中心化使用

* ============================================================
* 题 1 之一：4.3.2 虚拟变量 × 定量变量（式 4.23）
*   lnwage = b0 + b1*male + b2*educ + b3*male*educ + e
* ============================================================
* (1) 不设交互项：只检验截距差异
reg lnwage male educ
* (2) 模型（4.23）：Stata 的因子变量写法 i.male##c.educ 自动生成交互项
reg lnwage i.male##c.educ
estimates store m423
* (3) 等价的手工写法
gen male_educ = male*educ
reg lnwage male educ male_educ
estimates store m423b
estimates table m423 m423b, b(%9.4f) se(%9.4f) stats(N r2) 

* 式（4.24）偏效应 dlnwage/deduc = b2 + b3*male
* 式（4.25）偏效应 dlnwage/dmale = b1 + b3*educ
lincom educ + male_educ                  // 男性教育回报
lincom educ                              // 女性教育回报
display as text "式4.25：某 educ 处 male 的偏效应"
foreach e in 0 6 9 12 15 16 19 {
    display as text "  educ = " %2.0f `e' " 时 dlnwage/dmale = " %7.4f _b[male] + _b[male_educ]*`e'
}
* Stata 的 margins：样本均值处的偏效应（对应式 4.28 的 a1）
margins, dydx(male) atmeans
margins, dydx(educ) atmeans
estimates restore m423
* 因子变量写法的 margins 同样给出均值处的性别效应（与式 4.26 的 a1 对照）
margins, dydx(1.male) atmeans

* (4) 中心化：4.26 / 4.27，male 的系数变成“教育均值处的性别差异”
quietly summarize educ
local m_educ = r(mean)
gen c_educ = educ - `m_educ'
gen male_c_educ = male*c_educ
reg lnwage male educ male_c_educ         // 对应模型（4.26）
estimates store m426
reg lnwage i.male##c.c_educ              // 对应模型（4.27）
estimates store m427
estimates table m423 m426 m427, b(%9.4f) se(%9.4f) stats(N r2)
display as text "educ 均值 = " %8.4f `m_educ'

* ============================================================
* 题 1 之二：4.3.3 定量变量 × 定量变量（式 4.29—4.33）
*   lnwage = b0 + b1*lnpop + b2*educ + b3*lnpop*educ + e
* ============================================================
* (5) 只有主效应
reg lnwage lnpop educ
* (6) 手工写法：先自己生成乘积项，系数名就是 lnpop_x_educ，便于用 _b[] 计算偏效应
gen lnpop_x_educ = lnpop*educ
reg lnwage lnpop educ lnpop_x_educ
estimates store m429
* 式（4.30）偏效应：dlnwage/dlnpop = b1 + b3*educ
display as text "式4.30：不同教育年限下城市规模的工资弹性"
foreach e in 6 9 12 15 16 19 {
    display as text "  educ = " %2.0f `e' " 年时城市规模弹性 = " ///
        %7.4f _b[lnpop] + _b[lnpop_x_educ]*`e'
}
* 同样可以用 lincom 给出标准误（以 educ = 16 年为例）
lincom lnpop + 16*lnpop_x_educ
* 式（4.30）另一个偏效应：dlnwage/deduc = b2 + b3*lnpop
foreach p in 4 5 6 7 8 {
    display as text "  lnpop = " %1.0f `p' " 时教育回报 = " ///
        %7.4f _b[educ] + _b[lnpop_x_educ]*`p'
}
* margins 的正确用法：educ 出现在模型中，但它的偏效应不随 educ 自身变化，
* 所以要用 at(lnpop=(...)) 才能看到（4.30）中 dlnwage/deduc 随 lnpop 的变化
margins, dydx(educ) at(lnpop=(4 5 6 7 8))
* 而 dydx(lnpop) 不随 educ 设置 at() 而改变，只能手工计算（见上式 foreach）

* (7) 模型（4.31）/（4.32）：中心化后再相乘，交互项系数不变
quietly summarize lnpop
local m_lnpop = r(mean)
gen c_lnpop = lnpop - `m_lnpop'
gen clnpop_x_ceduc = c_lnpop*c_educ
reg lnwage c_lnpop c_educ clnpop_x_ceduc          // 模型（4.31）
estimates store m431
reg lnwage c.lnpop##c.c_educ                      // 模型（4.32）
estimates store m432
estimates table m429 m431 m432, b(%9.4f) se(%9.4f) stats(N r2)
display as text "lnpop 均值 = " %8.4f `m_lnpop' "，educ 均值 = " %8.4f `m_educ'
* 式（4.33）：中心化后主效应 = 另一变量取均值时的偏效应
estimates restore m432
margins, dydx(lnpop c_educ) atmeans

* ============================================================
* 题 2：4.5 Stata 应用（式 4.37A / 4.37B）
*   lnwage = b0 + b1*lnpop + b2*educ + b3*lnpop*educ
*            + b4*male + b5*marr + b6*exp + b7*exp2
*            + 健康虚拟变量 + 行业 FE + 职业 FE + e
* ============================================================
* (8) 先看等价写法：reg + 全部虚拟变量（行业 20 类、职业 8 类）
reg lnwage c.lnpop##c.educ male marr exp exp2 i.health i.hangye i.zhiye
estimates store m_reg
* (9) 式 4.37A：reghdfe 把行业、职业固定效应“吸收”掉，等价于上式
*     说明：因子变量写法的交互项系数名是 c.lnpop#c.educ，reghdfe 存估计后
*     既不能写 _b[lnpop_x_educ]，也不能用 _b[c.lnpop#c.educ]（名称被拼接），
*     所以下面同时跑一份“手工乘积项”的版本，偏效应全部用它计算。
gen lnpop_x_educ_2 = lnpop*educ
reghdfe lnwage c.lnpop##c.educ male marr exp exp2 i.health, absorb(hangye zhiye)
estimates store m437A
reghdfe lnwage lnpop educ lnpop_x_educ male marr exp exp2 i.health, absorb(hangye zhiye)
estimates store m437A2
* 主效应模型的对照（不含交互项）
reghdfe lnwage lnpop educ male marr exp exp2 i.health, absorb(hangye zhiye)
estimates store m437base
* (10) 偏效应：margins, dydx(...) atmeans（样本均值处）
*     注意：reghdfe 之后 margins 对交互项的 at() 设定失效，所以偏效应一律手工算
estimates restore m437A2
display as text "式4.30：不同教育年限下城市规模的工资弹性"
foreach e in 6 9 12 15 16 19 {
    display as text "  educ = " %2.0f `e' " 年：城市规模弹性 = " ///
        %7.4f _b[lnpop] + _b[lnpop_x_educ]*`e' 
}
foreach p in 4 5 6 7 8 {
    display as text "  lnpop = " %1.0f `p' " 时教育回报 = " ///
        %7.4f _b[educ] + _b[lnpop_x_educ]*`p'
}
lincom lnpop + 16*lnpop_x_educ
* 用 margins 交叉核对：先 set obs 无关，改在普通 reg 下做（无固定效应，见 (8)）
estimates restore m_reg
margins, dydx(lnpop) at(educ=(6 9 12 15 16 19))
margins, dydx(educ) at(lnpop=(4 5 6 7 8))
margins, dydx(lnpop educ) atmeans

* (11) 式 4.37B：center 生成中心化变量 c_lnpop、c_educ 后重新估计
capture drop c_lnpop c_educ
center lnpop educ
reghdfe lnwage c.c_lnpop##c.c_educ male marr exp exp2 i.health, absorb(hangye zhiye)
estimates store m437B
* 两个模型的对照：交互项系数完全相同，主效应变为均值处的偏效应
estimates table m437base m437A m437B, b(%9.4f) se(%9.4f) stats(N r2)
estimates restore m437B
margins, dydx(c_lnpop c_educ) atmeans

* (12) 稳健性：按教育分组回归，看城市规模溢价是否随教育上升
reg lnwage lnpop educ male marr exp exp2 i.health i.hangye i.zhiye ///
    if educ <= 9
estimates store e_low
reg lnwage lnpop educ male marr exp exp2 i.health i.hangye i.zhiye ///
    if educ >= 15
estimates store e_high
estimates table e_low e_high, b(%9.4f) se(%9.4f) stats(N r2)

log close
exit
