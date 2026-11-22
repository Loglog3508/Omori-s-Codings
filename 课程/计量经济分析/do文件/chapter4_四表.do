*==============================================================
* 计量经济分析 · 第四章「函数形式的确定」
* 四个表：表一 描述性统计 / 表二 双变量与多元回归对比
*         表三 虚拟变量加法模型 / 表四 虚拟变量乘法模型
*
* 数据：实验一\CMDS2017子样本.dta   N = 14,757
*   变量：male eduyear exp exp2 marriage lnpop lnwage
*   lnpop  = ln(城市人口/1000)，129 个城市
*   lnwage = ln(月工资)
*
* 运行：在 Stata 中 do 本文件；表格输出需要 estout
*   （ssc install estout），未安装时脚本仍会打印全部结果
* 输出：输出\表1_描述性统计.csv
*       输出\表2_回归对比.rtf
*       输出\表3_加法模型.rtf
*       输出\表4_乘法模型.rtf
*==============================================================
clear all
set more off
capture log close

* 注意：global 名不要用 path、root 等系统环境变量名，
*       否则会被 Stata 展开成环境变量的值
global base "C:/Users/omori/Omori-s-Codings/课程/计量经济分析"
global out  "${base}/输出"
capture mkdir "${out}"

capture which estout
local has_estout = (_rc == 0)
if !`has_estout' {
    di as error "未找到 estout，请先 ssc install estout；脚本仍会运行并显示结果"
}

*--------------------------------------------------------------
* 0. 读数据、生成新变量
*    注意：Stata 的 drop 按前缀匹配，临时变量名不要与已有变量
*          互为前缀（如 spm 不与 exp2/male/marr 冲突）
*--------------------------------------------------------------
use "${base}/实验一/CMDS2017子样本.dta", clear

rename marriage spm                      // 婚姻（0/1）
rename eduyear   sedu                    // 受教育年限
gen double marr = spm + 0                // 0/1 虚拟变量：已婚=1
gen double educ = sedu + 0               // 受教育年限
capture drop exp2
gen double exp2 = exp^2                  // 经验平方（重算为 double，保证精度）

* 交互项
gen double male_x_marr  = male * marr    // 性别 × 婚姻
gen double male_x_educ  = male * educ    // 性别 × 教育
gen double lnpop_x_educ = lnpop * educ   // 城市规模 × 教育（例 4.37A）
gen double lnpop_x_male = lnpop * male   // 城市规模 × 性别
gen double lnpop_x_marr = lnpop * marr   // 城市规模 × 婚姻

* 中心化（例 4.37B）
egen double m_lnpop = mean(lnpop)
egen double m_educ  = mean(educ)
gen double c_lnpop  = lnpop - m_lnpop
gen double c_educ   = educ  - m_educ
gen double clnpop_x_ceduc = c_lnpop * c_educ

count                                    // 14,757
di "lnpop 均值 = " %8.3f m_lnpop[1] "   educ 均值 = " %8.3f m_educ[1]

*--------------------------------------------------------------
* 表 1  描述性统计
*--------------------------------------------------------------
estpost tabstat male educ exp exp2 marr lnpop lnwage, ///
    stat(n mean sd min max) columns(statistics)
if `has_estout' {
    esttab using "${out}/表1_描述性统计.csv", replace ///
        cells("count(fmt(%9.0fc)) mean(fmt(%9.3f)) sd(fmt(%9.3f)) min(fmt(%9.3f)) max(fmt(%9.3f))") noobs nonumber nomtitle plain ///
        collabels("Obs" "Mean" "SD" "Min" "Max") varlabels(male male educ educ exp exp exp2 exp2 marr marr lnpop lnpop lnwage lnwage)
}
esttab, cells("count(fmt(%9.0fc)) mean(fmt(%9.3f)) sd(fmt(%9.3f)) min(fmt(%9.3f)) max(fmt(%9.3f))") noobs nonumber nomtitle collabels("Obs" "Mean" "SD" "Min" "Max") varlabels(male male educ educ exp exp exp2 exp2 marr marr lnpop lnpop lnwage lnwage)

* 城市规模四分位：看大城市是否工资更高
preserve
    xtile q1 = lnpop, nq(4)
    table q1, statistic(freq) statistic(mean lnpop) statistic(mean lnwage) ///
        statistic(mean educ)
restore

* 分组均值（用于表四的直观对照）
table male, statistic(mean lnwage) statistic(sd lnwage) statistic(freq)
table marr, statistic(mean lnwage) statistic(sd lnwage) statistic(freq)

*--------------------------------------------------------------
* 表 2  双变量回归与多元回归的对比
*--------------------------------------------------------------
eststo clear
eststo t2a: quietly reg lnwage lnpop                                // (1) 双变量
eststo t2b: quietly reg lnwage lnpop educ                           // (2) 加教育
eststo t2c: quietly reg lnwage lnpop educ male marr exp exp2        // (3) 加全部控制
eststo t2d: quietly reg lnwage lnpop educ lnpop_x_educ male marr exp exp2  // (4) 加交互项
if `has_estout' {
    esttab t2a t2b t2c t2d using "${out}/表2_回归对比.rtf", replace ///
        b(3) se(3) star(* 0.10 ** 0.05 *** 0.01) r2(%9.3f) obslast ///
        keep(lnpop educ male marr exp exp2 lnpop_x_educ _cons) ///
        mtitles("(1) 双变量" "(2) 加教育" "(3) 全部控制" "(4) 加交互项") ///
        title("表2  双变量与多元回归对比（因变量：lnwage）")
}
esttab t2a t2b t2c t2d, b(3) se(3) star(* 0.10 ** 0.05 *** 0.01) r2(%9.3f) obslast ///
    keep(lnpop educ male marr exp exp2 lnpop_x_educ _cons) ///
    mtitles("(1)" "(2)" "(3)" "(4)")

* 弹性与半弹性的精确百分比换算
quietly reg lnwage lnpop
di "lnpop 弹性 0.114 -> 城市人口多 10% 工资高 " %6.2f 100*(1.1^_b[lnpop]-1) "%"
quietly reg lnwage lnpop educ male marr exp exp2
di "educ 系数 = " %8.4f _b[educ] "  精确百分比 = " %6.2f 100*(exp(_b[educ])-1) "%"
di "male 系数 = " %8.4f _b[male] "  精确百分比 = " %6.2f 100*(exp(_b[male])-1) "%"
di "marr 系数 = " %8.4f _b[marr] "  精确百分比 = " %6.2f 100*(exp(_b[marr])-1) "%"
di "经验转折点 exp = " %8.2f -_b[exp]/(2*_b[exp2])

*--------------------------------------------------------------
* 表 3  虚拟变量加法模型（只改变截距、不改变斜率）
*--------------------------------------------------------------
eststo clear
eststo t3a: quietly reg lnwage male                                  // (1) 只放性别
eststo t3b: quietly reg lnwage marr                                  // (2) 只放婚姻
eststo t3c: quietly reg lnwage male marr                             // (3) 两个虚拟变量
eststo t3d: quietly reg lnwage lnpop educ male marr exp exp2         // (4) 加全部控制
eststo t3e: quietly reg lnwage lnpop educ male marr                  // (5) 最简加法形式
if `has_estout' {
    esttab t3a t3b t3c t3d t3e using "${out}/表3_加法模型.rtf", replace ///
        b(3) se(3) star(* 0.10 ** 0.05 *** 0.01) r2(%9.3f) obslast ///
        keep(lnpop educ male marr exp exp2 _cons) ///
        mtitles("(1) male" "(2) marr" "(3) male+marr" "(4) 全控制" "(5) 简式") ///
        title("表3  虚拟变量加法模型（因变量：lnwage）")
}
esttab t3a t3b t3c t3d t3e, b(3) se(3) star(* 0.10 ** 0.05 *** 0.01) r2(%9.3f) obslast ///
    keep(lnpop educ male marr exp exp2 _cons) mtitles("(1)" "(2)" "(3)" "(4)" "(5)")

* 虚拟变量的精确百分比（lnY 下的系数 = 半弹性）
quietly reg lnwage male
di "male 单独放入的精确百分比 = " %6.2f 100*(exp(_b[male])-1) "%"
quietly reg lnwage marr
di "marr 单独放入的精确百分比 = " %6.2f 100*(exp(_b[marr])-1) "%"

*--------------------------------------------------------------
* 表 4  虚拟变量乘法模型（截距与斜率同时改变）
*--------------------------------------------------------------
eststo clear
eststo t4a: quietly reg lnwage male marr male_x_marr                        // (1) male×marr
eststo t4b: quietly reg lnwage male educ male_x_educ                        // (2) male×educ
eststo t4c: quietly reg lnwage lnpop educ lnpop_x_educ male marr exp exp2      // (3) 例4.37A
quietly reg lnwage lnpop educ lnpop_x_educ male marr exp exp2
scalar bp = _b[lnpop]
scalar bl = _b[lnpop_x_educ]
scalar be = _b[educ]
eststo t4d: quietly reg lnwage c_lnpop c_educ clnpop_x_ceduc male marr exp exp2  // (4) 例4.37B 中心化
eststo t4e: quietly reg lnwage lnpop educ male marr exp exp2 ///
    lnpop_x_male lnpop_x_marr                                               // (5) lnpop×male、lnpop×marr
if `has_estout' {
    esttab t4a t4b t4c t4d t4e using "${out}/表4_乘法模型.rtf", replace ///
        b(3) se(3) star(* 0.10 ** 0.05 *** 0.01) r2(%9.3f) obslast ///
        keep(male marr male_x_marr educ male_x_educ lnpop c_lnpop c_educ ///
             lnpop_x_educ clnpop_x_ceduc lnpop_x_male lnpop_x_marr exp exp2 _cons) ///
        mtitles("(1) male*marr" "(2) male*educ" "(3) 4.37A" "(4) 4.37B" "(5) lnpop*male/marr") ///
        title("表4  虚拟变量乘法模型（因变量：lnwage）")
}
esttab t4a t4b t4c t4d t4e, b(3) se(3) star(* 0.10 ** 0.05 *** 0.01) r2(%9.3f) obslast ///
    keep(male marr male_x_marr educ male_x_educ lnpop c_lnpop c_educ ///
         lnpop_x_educ clnpop_x_ceduc lnpop_x_male lnpop_x_marr exp exp2 _cons) ///
    mtitles("(1)" "(2)" "(3)" "(4)" "(5)")

* 列(1) 四组截距
quietly reg lnwage male marr male_x_marr
scalar a0 = _b[_cons]
scalar am = _b[male]
scalar aw = _b[marr]
scalar amw = _b[male_x_marr]
di "未婚女性 = " %8.3f a0
di "未婚男性 = " %8.3f a0 + am
di "已婚女性 = " %8.3f a0 + aw
di "已婚男性 = " %8.3f a0 + am + aw + amw
di "已婚相对未婚（女性）百分比 = " %6.2f 100*(exp(aw)-1) "%"
di "已婚相对未婚（男性）百分比 = " %6.2f 100*(exp(aw+amw)-1) "%"
di "男性相对女性（已婚）百分比 = " %6.2f 100*(exp(am+amw)-1) "%"

* 列(3) lnpop 的边际效应 = bp + bl*educ（随教育年限变化）
foreach k of numlist 6 9 12 14 16 19 {
    di "educ = " %3.0f `k' " 时 lnpop 边际效应 = " %8.4f bp + bl*`k'
}

* 交互项的嵌套模型 F 检验：受限模型不含交互项
quietly reg lnwage lnpop educ male marr exp exp2
estimates store restr
quietly reg lnwage lnpop educ lnpop_x_educ male marr exp exp2
estimates store unrest
lrtest restr unrest                        // 或：test lnpop_x_educ
test lnpop_x_educ
di "交互项显著性 p = " %9.3e r(p)

di "全部四个表已输出到 ${out}"
