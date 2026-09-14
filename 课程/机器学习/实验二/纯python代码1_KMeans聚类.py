"""
实验二 纯python代码1：使用 numpy 从零实现 K-Means 聚类算法（并对其改进）

仅使用 numpy 实现，不依赖 sklearn 等机器学习框架。
基本原理（Lloyd 算法）：
    1. 初始化：选定 K 个聚类中心；
    2. 分配：把每个样本分配到距离最近的中心，得到簇标签；
    3. 更新：把每个中心移动到其簇内所有样本的均值位置；
    4. 重复 2~3 步，直到中心不再变化（或变化很小）。
    目标函数（簇内误差平方和 SSE / 惯性 inertia）：
        J = Σ_j Σ_{x∈C_j} || x - μ_j ||^2

相对基础版本的 5 点改进：
    改进1：k-means++ 初始化——按“到已有中心距离的平方”做加权随机抽样来选中心，
           并对每个新中心抽取多个候选、取平方距离和下降最多的那个（贪心 k-means++），让初始中心彼此远离，明显降低陷入较差局部最优的概率；
    改进2：n_init 多次重启——用不同随机种子跑多遍，取 SSE 最小的一次，
           使聚类结果对初始化不再敏感；
    改进3：收敛判据——当中心最大位移小于 tolerance 时提前停止，
           不必固定跑满迭代次数（同时记录每轮 SSE，便于画收敛曲线）；
    改进4：空簇处理——若某个簇分不到样本，则把该中心重置到“离最近中心最远”
           的样本上，避免出现无意义的中心；
    改进5：向量化距离计算 + 轮廓系数——用矩阵运算一次性算完所有样本到所有中心的
           距离（||x-c||^2 = ||x||^2 - 2x·c + ||c||^2），并内置纯 numpy 的轮廓系数，
           便于选择簇数 K。
"""
import numpy as np


class KMeans:
    """K-Means 聚类（numpy 实现，含 k-means++ 初始化与多次重启）"""

    def __init__(self, n_clusters=3, n_init=10, max_iter=300, tolerance=1e-4,
                 init="k-means++", random_state=42):
        self.n_clusters = n_clusters          # 簇数 K
        self.n_init = n_init                  # 重启次数（改进2）
        self.max_iter = max_iter              # 单次运行的最大迭代次数
        self.tolerance = tolerance            # 中心位移收敛阈值（改进3）
        self.init = init                      # "k-means++"（改进1）或 "random"
        self.random_state = random_state
        self.cluster_centers_ = None          # (K, n) 簇中心
        self.labels_ = None                   # (m,) 每个样本的簇标签
        self.inertia_ = None                  # 最优一次的 SSE
        self.n_iter_ = None                   # 最优一次实际迭代轮数
        self.inertia_history_ = []            # 最优一次每轮 SSE，用于观察收敛

    # ---------------------------------------------------------------- 距离
    @staticmethod
    def _distances_to_centers(X, centers):
        """返回每个样本到每个中心的欧氏距离平方，形状 (m, K)（改进5 向量化）"""
        x_sq = np.sum(X ** 2, axis=1, keepdims=True)              # (m, 1)
        c_sq = np.sum(centers ** 2, axis=1, keepdims=True).T      # (1, K)
        d2 = x_sq - 2.0 * X @ centers.T + c_sq
        return np.maximum(d2, 0.0)                               # 数值误差可能产生极小负数
    # ------------------------------------------------------------ 初始化
    def _kmeans_plusplus(self, X, rng):
        """k-means++ 初始化（改进1）：让初始中心彼此尽量远离"""
        m, n = X.shape
        k = self.n_clusters
        centers = np.empty((k, n), dtype=float)

        # 第 1 个中心随机取一个样本
        centers[0] = X[rng.integers(m)]
        closest = self._distances_to_centers(X, centers[:1]).ravel()

        n_local_trials = 2 + int(np.log(k))       # 每个新中心抽取的候选个数
        for i in range(1, k):
            total = closest.sum()
            if total <= 0:
                # 剩余样本与已有中心全部重合，只能随机补一个
                centers[i] = X[rng.integers(m)]
                continue
            # 到已有中心距离平方越大，被选为新中心的概率越大
            probs = closest / total
            candidates = rng.choice(m, size=n_local_trials, p=probs)
            # 贪心：在多个候选里选“加入后平方距离和最小”的那个
            best_potential, best_idx = np.inf, int(candidates[0])
            for idx in candidates:
                d_new = self._distances_to_centers(X, X[idx:idx + 1]).ravel()
                potential = float(np.minimum(closest, d_new).sum())
                if potential < best_potential:
                    best_potential, best_idx = potential, int(idx)
            centers[i] = X[best_idx]
            d_new = self._distances_to_centers(X, centers[i:i + 1]).ravel()
            closest = np.minimum(closest, d_new)
        return centers

    def _init_centers(self, X, rng):
        if self.init == "k-means++":
            return self._kmeans_plusplus(X, rng)
        # 基础版本：随机挑 K 个不重复的样本作为中心
        idx = rng.choice(X.shape[0], size=self.n_clusters, replace=False)
        return X[idx].astype(float).copy()

    # -------------------------------------------------------------- 单次运行
    def _single_run(self, X, rng):
        centers = self._init_centers(X, rng)
        history = []
        m = X.shape[0]

        for it in range(1, self.max_iter + 1):
            # 分配步：每个样本归到最近的中心
            d2 = self._distances_to_centers(X, centers)
            labels = np.argmin(d2, axis=1)
            history.append(float(d2[np.arange(m), labels].sum()))

            # 更新步：中心移动到簇内样本均值
            new_centers = centers.copy()
            for j in range(self.n_clusters):
                mask = labels == j
                if np.any(mask):
                    new_centers[j] = X[mask].mean(axis=0)
                else:
                    # 改进4：空簇处理，挑离最近中心最远的样本作为新中心
                    own = np.min(self._distances_to_centers(X, centers), axis=1)
                    farthest = int(np.argmax(own))
                    new_centers[j] = X[farthest]
                    labels[farthest] = j

            # 改进3：中心位移足够小则认为收敛
            shift = float(np.max(np.linalg.norm(new_centers - centers, axis=1)))
            centers = new_centers
            if shift < self.tolerance:
                break

        # 用最终中心重新分配，得到稳定的标签与 SSE
        d2 = self._distances_to_centers(X, centers)
        labels = np.argmin(d2, axis=1)
        inertia = float(d2[np.arange(m), labels].sum())
        history.append(inertia)
        return centers, labels, inertia, history, it
    # ---------------------------------------------------------------- 训练
    def fit(self, X):
        X = np.asarray(X, dtype=float)
        if self.n_clusters > X.shape[0]:
            raise ValueError("簇数 K 不能大于样本数")

        best = None
        for run in range(self.n_init):          # 改进2：多次重启取 SSE 最小
            rng = np.random.default_rng(self.random_state + run)
            centers, labels, inertia, history, n_iter = self._single_run(X, rng)
            if best is None or inertia < best[2]:
                best = (centers, labels, inertia, history, n_iter)

        self.cluster_centers_, self.labels_, self.inertia_, \
            self.inertia_history_, self.n_iter_ = best
        return self

    def fit_predict(self, X):
        return self.fit(X).labels_

    def predict(self, X):
        """把新样本分配到距离最近的中心"""
        X = np.asarray(X, dtype=float)
        return np.argmin(self._distances_to_centers(X, self.cluster_centers_), axis=1)

    def transform(self, X):
        """返回样本到各中心的欧氏距离矩阵，形状 (m, K)"""
        X = np.asarray(X, dtype=float)
        return np.sqrt(self._distances_to_centers(X, self.cluster_centers_))

    def score(self, X):
        """返回负的 SSE（越大越好）"""
        X = np.asarray(X, dtype=float)
        d2 = self._distances_to_centers(X, self.cluster_centers_)
        return -float(d2[np.arange(X.shape[0]), np.argmin(d2, axis=1)].sum())


def silhouette_score(X, labels):
    """纯 numpy 实现的轮廓系数（改进5），取值 [-1, 1]，越大说明簇内越紧凑、簇间越分离

    对每个样本 i：
        a(i) = i 到同簇其他样本的平均距离（簇内不相似度）
        b(i) = i 到“最近的其他簇”中所有样本的平均距离（簇间不相似度）
        s(i) = (b(i) - a(i)) / max(a(i), b(i))
    轮廓系数 = 所有样本 s(i) 的平均值。
    注意：需要 O(n^2) 的距离矩阵，样本量很大时不建议使用。
    """
    X = np.asarray(X, dtype=float)
    labels = np.asarray(labels).ravel()
    n = X.shape[0]
    unique = np.unique(labels)
    if unique.size < 2 or unique.size >= n:
        raise ValueError("轮廓系数要求簇数在 2 到 n-1 之间")

    diff = X[:, None, :] - X[None, :, :]
    dist = np.sqrt(np.sum(diff ** 2, axis=-1))

    scores = np.zeros(n)
    for i in range(n):
        same = labels == labels[i]
        same[i] = False
        a = dist[i, same].mean() if np.any(same) else 0.0
        b = min(dist[i, labels == c].mean() for c in unique if c != labels[i])
        denom = max(a, b)
        scores[i] = (b - a) / denom if denom > 0 else 0.0
    return float(scores.mean())


if __name__ == "__main__":
    # -------------------------------------------- 自测1：三个高斯簇
    rng = np.random.default_rng(0)
    X = np.vstack([
        rng.normal(loc=(-6, -6), scale=1.0, size=(100, 2)),
        rng.normal(loc=(0, 6), scale=1.0, size=(100, 2)),
        rng.normal(loc=(6, -6), scale=1.0, size=(100, 2)),
    ])
    y_true = np.repeat([0, 1, 2], 100)

    model = KMeans(n_clusters=3, n_init=10, random_state=42).fit(X)
    print("纯python代码1自测：SSE =", round(model.inertia_, 4),
          "，迭代轮数 =", model.n_iter_)
    print("轮廓系数 =", round(silhouette_score(X, model.labels_), 4))
    # 用“多数投票”把簇标签对齐到真实标签，算一个聚类准确率
    acc = sum(
        np.bincount(y_true[model.labels_ == j]).max()
        for j in range(3)
    ) / len(y_true)
    print("聚类准确率（投票对齐后）= ", round(float(acc), 4))

    # ------------------------- 自测2：改进1/2 的效果——多次实验比较 SSE
    def run_many(init):
        sses = []
        for seed in range(20):
            km = KMeans(n_clusters=3, n_init=1, init=init, random_state=seed).fit(X)
            sses.append(km.inertia_)
        return np.array(sses)

    sse_random = run_many("random")
    sse_pp = run_many("k-means++")
    print("\n随机初始化    ：SSE 均值 = %.2f，标准差 = %.2f，最差 = %.2f"
          % (sse_random.mean(), sse_random.std(), sse_random.max()))
    print("k-means++ 初始化：SSE 均值 = %.2f，标准差 = %.2f，最差 = %.2f"
          % (sse_pp.mean(), sse_pp.std(), sse_pp.max()))
    print("=> k-means++ 初始化更稳定、更不容易陷入较差局部最优（改进1 有效）")