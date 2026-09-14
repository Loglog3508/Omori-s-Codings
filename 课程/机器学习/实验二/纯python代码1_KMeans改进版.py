"""
实验二 纯python代码1（改进版）：在老师提供的 kmeans.py 基础上改进 K-Means 聚类算法

老师提供的原始代码：KMeans/纯python代码1/kmeans.py（原文件未做任何改动）
    其中已经实现了 K-Means 的核心流程，而且做得不错：
        - _init_centers_kpp()：k-means++ 初始化簇中心；
        - predict()：n_init 次重启，取 SSE 最小的一次；
        - _kmeans() 第 3 步：用中心位移阈值 tol 判断是否收敛；
        - _kmeans() 第 2 步：发现空簇时返回 None，由 predict() 重新运行。

本文件不改动老师的原文件，而是用“继承 + 重写关键方法”的方式在其基础上做 5 点改进：

    改进1：兼容性与可复现性
           老师代码用了 np.int 与 np.object 这两个别名，而它们从 NumPy 1.24 起被弃用、
           2.0 起被彻底移除，在 NumPy 2.x 上会直接抛 AttributeError 而跑不起来；
           改用 Python 内置的 int / object。
           同时新增 random_state 参数固定随机种子，让结果可复现、可对比。

    改进1 续：更稳的 k-means++
           老师的 _init_centers_kpp 直接按距离平方做一次加权抽样；这里改为每个新中心先抽
           n_local_trials = 2 + ln(k) 个候选，再取“加进去之后平方距离和最小”的那个
           （贪心策略，与 sklearn 的做法一致），初始中心更分散，最终 SSE 更小更稳定。

    改进2：空簇处理
           老师代码遇到空簇就返回 None，再由 predict() 里的 while res is None
           反复重跑，运气不好时会反复失败、浪费时间；
           这里改为把空簇中心重置到最“孤单”的样本上（作为种子把样本吸引过来），
           并在最后检查一遍，保证输出结果真的是 k 个非空簇。

    改进3：收敛判据与过程记录
           除了中心位移阈值，还把每轮的目标函数 J（SSE）记录下来，
           既能看到“J 单调不增”的性质，也能画收敛曲线。

    改进4：向量化距离计算
           老师代码用一个 for 循环逐簇计算距离，这里改成矩阵运算
           ||x-c||^2 = ||x||^2 - 2x·c + ||c||^2 一次算完所有样本到所有中心的距离，更快。

    改进5：SSE 计算修正 + 轮廓系数
           老师代码最后 sse = np.sum(distances[range(m), labels]) 用的还是“更新中心之前”
           那一次分配留下的距离矩阵，数值偏大；这里用最终中心重新分配后再算 SSE。
           另外内置了纯 numpy 的轮廓系数，方便配合肘部法选择簇数 K。

用法与老师代码保持一致：
    km = ImprovedKMeans(k_clusters=3, random_state=42)
    labels = km.predict(X)          # 返回每个样本的簇标签
    km.centers_                     # 簇中心
    km.sse_                         # 目标函数 J（簇内误差平方和）
    km.n_iter_ / km.sse_history_    # 实际迭代轮数 / 每轮 J（改进3）
"""
import numpy as np

from kmeans import KMeans as BaseKMeans


class ImprovedKMeans(BaseKMeans):
    """在老师提供的 KMeans 基础上改进的版本（继承并重写关键方法）"""

    def __init__(self, k_clusters, tol=1e-4, max_iter=300, n_init=10,
                 init="k-means++", random_state=None):
        # 先沿用老师的 4 个参数（k_clusters / tol / max_iter / n_init）
        super().__init__(k_clusters, tol=tol, max_iter=max_iter, n_init=n_init)
        # 改进1：新增随机种子保证可复现；init 可选 "k-means++" 或 "random"（便于对比）
        self.init = init
        self.random_state = random_state
        # 训练后得到的属性（名字与老师代码保持一致）
        self.centers_ = None
        self.sse_ = None
        self.labels_ = None
        # 新增：实际迭代轮数与每轮的目标函数 J（改进3）
        self.n_iter_ = 0
        self.sse_history_ = []

    # ------------------------------------------------ 改进4：一次算完所有距离
    @staticmethod
    def _sq_dists(X, centers):
        """返回每个样本到每个中心的欧氏距离平方，形状 (m, k)"""
        x_sq = np.sum(X ** 2, axis=1, keepdims=True)
        c_sq = np.sum(centers ** 2, axis=1, keepdims=True).T
        return np.maximum(x_sq - 2.0 * X @ centers.T + c_sq, 0.0)

    # ------------------------------------------------ 改进1：可复现的 k-means++
    def _init_centers_kpp(self, X, n_clusters, rng):
        """k-means++ 初始化（重写老师的方法：改用传入的随机数发生器，结果可复现）"""
        m, n = X.shape
        centers = np.empty((n_clusters, n))
        # 随机选第一个簇中心
        centers[0] = X[rng.integers(m)]
        # 每个样本到“已有中心中最近那个”的距离平方
        closest = self._sq_dists(X, centers[:1]).ravel()

        # 每个新中心先按权重抽几个候选，再挑“加进去以后平方距离和最小”的那个（贪心）
        n_local_trials = 2 + int(np.log(n_clusters))
        for j in range(1, n_clusters):
            total = closest.sum()
            if total <= 0:
                centers[j] = X[rng.integers(m)]
                continue
            # 以距离平方为权重做抽样：离已有中心越远的样本越可能被选为新中心
            probs = closest / total
            candidates = rng.choice(m, size=n_local_trials, p=probs)
            best_potential, best_idx = np.inf, int(candidates[0])
            for idx in candidates:
                d_new = self._sq_dists(X, X[idx:idx + 1]).ravel()
                potential = float(np.minimum(closest, d_new).sum())
                if potential < best_potential:
                    best_potential, best_idx = potential, int(idx)
            centers[j] = X[best_idx]
            closest = np.minimum(closest, self._sq_dists(X, centers[j:j + 1]).ravel())
        return centers

    def _init_centers_random(self, X, rng):
        """对照用：随机挑 k 个互不相同的样本作为初始中心"""
        idx = rng.choice(X.shape[0], size=self.k_clusters, replace=False)
        return X[idx].astype(float).copy()

    def _init_centers(self, X, rng):
        if self.init == "k-means++":
            return self._init_centers_kpp(X, self.k_clusters, rng)
        return self._init_centers_random(X, rng)

    # ------------------------------------------------ 改进2/3/5：核心算法
    def _kmeans(self, X, rng):
        """K-Means 核心算法（重写老师的方法：修复空簇 + 记录 J + 修正 SSE）"""
        m = X.shape[0]
        centers = self._init_centers(X, rng)
        sse_history = []

        for it in range(1, self.max_iter + 1):
            # 1. 分配标签：每个样本划给距离最近的中心
            d2 = self._sq_dists(X, centers)
            labels = np.argmin(d2, axis=1)
            # 改进3：记录本轮目标函数 J（各样本到其所属中心距离平方之和）
            sse_history.append(float(d2[np.arange(m), labels].sum()))

            # 2. 计算重心
            new_centers = centers.copy()
            for j in range(self.k_clusters):
                mask = labels == j
                if np.any(mask):
                    new_centers[j] = X[mask].mean(axis=0)
                else:
                    # 改进2：空簇不再返回 None 重跑，而是把中心挪到最“孤单”的样本上，
                    # 作为“种子”在下一轮把样本吸引过来
                    far = int(np.argmax(d2[np.arange(m), labels]))
                    new_centers[j] = X[far]

            # 3. 判断收敛：所有中心的位移都小于容忍度就提前结束
            shift = float(np.max(np.linalg.norm(new_centers - centers, axis=1)))
            centers = new_centers
            if shift < self.tol:
                break

        # 改进5：用最终中心重新分配后再算 SSE（老师代码此处用的是更新中心之前那一次的距离）
        d2 = self._sq_dists(X, centers)
        labels = np.argmin(d2, axis=1)

        # 改进2（补充）：万一最终分配仍然留下空簇，就从“样本数最多的那个簇”里
        # 挪一个离自己中心最远的样本过去，保证结果真的是 k 个非空簇
        for j in range(self.k_clusters):
            if np.any(labels == j):
                continue
            sizes = np.bincount(labels, minlength=self.k_clusters)
            src = int(np.argmax(sizes))
            if sizes[src] <= 1:
                break                       # 已经没有可以拆分的簇了
            own = np.where(labels == src, d2[np.arange(m), labels], -1.0)
            labels[int(np.argmax(own))] = j

        # 用最终标签重算中心，保证簇中心就是簇内样本的均值
        centers = np.array([X[labels == j].mean(axis=0)
                            for j in range(self.k_clusters)])
        sse = float(np.sum((X - centers[labels]) ** 2))
        sse_history.append(sse)
        return labels, centers, sse, sse_history, it

    def predict(self, X):
        """反复运行 n_init 次，取 SSE 最小的一次作为最终结果（沿用老师的思路）"""
        X = np.asarray(X, dtype=float)
        if self.random_state is None:
            seed = int(np.random.default_rng().integers(2 ** 31))
        else:
            seed = int(self.random_state)

        best = None
        for i in range(self.n_init):
            # 改进1：每次重启使用不同的随机种子，但整体可复现
            rng = np.random.default_rng(seed + i)
            labels, centers, sse, sse_history, n_iter = self._kmeans(X, rng)
            # 空簇已经在 _kmeans 内部修复，这里不再需要 while 反复重跑
            if best is None or sse < best[2]:
                best = (labels, centers, sse, sse_history, n_iter)

        labels, self.centers_, self.sse_, self.sse_history_, self.n_iter_ = best
        self.labels_ = labels
        return labels

    def fit(self, X):
        """sklearn 风格的别名，便于链式调用"""
        self.predict(X)
        return self


def silhouette_score(X, labels, chunk=256):
    """纯 numpy 实现的轮廓系数（改进5），取值 [-1, 1]，越大说明簇内越紧凑、簇间越分离

    对每个样本 i：
        a(i) = i 到同簇其他样本的平均距离（簇内不相似度）
        b(i) = i 到“最近的其他簇”中所有样本的平均距离（簇间不相似度）
        s(i) = (b(i) - a(i)) / max(a(i), b(i))
    轮廓系数 = 所有样本 s(i) 的平均值。

    为节省内存，距离按 chunk 行一块一块地算，避免一次性开出 n×n 的大矩阵。
    """
    X = np.asarray(X, dtype=float)
    labels = np.asarray(labels).ravel()
    n = X.shape[0]
    uniq = np.unique(labels)
    if uniq.size < 2 or uniq.size >= n:
        raise ValueError("轮廓系数要求簇数在 2 到 n-1 之间")

    a = np.zeros(n)
    b = np.full(n, np.inf)

    for s in range(0, n, chunk):
        e = min(s + chunk, n)
        block_labels = labels[s:e]
        # 本块样本到全部样本的欧氏距离，形状 (块大小, n)
        d = np.sqrt(np.maximum(
            ((X[s:e, None, :] - X[None, :, :]) ** 2).sum(axis=-1), 0.0))
        a_block = np.zeros(e - s)
        b_block = np.full(e - s, np.inf)

        for c in uniq:
            cols = labels == c
            cnt = int(cols.sum())
            if cnt == 0:
                continue
            total_c = d[:, cols].sum(axis=1)        # 到簇 c 所有样本的距离之和
            is_c = block_labels == c
            if cnt > 1:
                # 簇内平均距离：扣掉“自己到自己”的那个 0
                a_block[is_c] = total_c[is_c] / (cnt - 1)
            if cnt < n:
                # 簇间平均距离：只对不属于簇 c 的样本有意义
                b_block[~is_c] = np.minimum(b_block[~is_c], total_c[~is_c] / cnt)

        a[s:e] = a_block
        b[s:e] = np.minimum(b[s:e], b_block)

    denom = np.maximum(a, b)
    s_values = np.where(denom > 0, (b - a) / np.where(denom > 0, denom, 1.0), 0.0)
    return float(s_values.mean())