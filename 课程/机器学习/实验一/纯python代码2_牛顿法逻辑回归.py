"""
实验一 纯python代码2：使用牛顿法（IRLS，迭代重加权最小二乘）从零实现逻辑回归

与代码1（梯度下降）不同，牛顿法利用二阶导数（Hessian 矩阵）信息，
每次迭代直接求解线性方程组，通常收敛更快、迭代次数更少。
更新公式：
    w_new = w - H^(-1) * g
其中
    g = X^T (ŷ - y)                     （一阶梯度）
    H = X^T W X                         （Hessian 矩阵，W 为对角阵 W_ii = ŷ_i(1 - ŷ_i)）
"""
import numpy as np


class LogisticRegressionNewton:
    """基于牛顿法（IRLS）的逻辑回归（二分类）"""

    def __init__(self, n_iterations=100, tolerance=1e-8, random_state=42):
        self.n_iterations = n_iterations
        self.tolerance = tolerance
        self.random_state = random_state
        self.w = None
        self.b = None
        self.loss_history = []

    def _sigmoid(self, z):
        z = np.clip(z, -500, 500)
        return 1.0 / (1.0 + np.exp(-z))

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float).ravel()
        m, n = X.shape

        # 将偏置并入权重向量，方便矩阵运算
        Xb = np.hstack([np.ones((m, 1)), X])
        rng = np.random.default_rng(self.random_state)
        theta = np.zeros(n + 1)

        for i in range(self.n_iterations):
            z = Xb @ theta
            y_hat = self._sigmoid(z)
            loss = -np.mean(y * np.log(y_hat + 1e-12) + (1 - y) * np.log(1 - y_hat + 1e-12))
            self.loss_history.append(loss)

            # 梯度 g = X^T (ŷ - y)
            g = Xb.T @ (y_hat - y)
            # Hessian H = X^T W X，W = diag(ŷ(1-ŷ))
            W = y_hat * (1 - y_hat)
            H = (Xb * W[:, None]).T @ Xb
            # 加微小对角项保证数值稳定
            H = H + 1e-9 * np.eye(n + 1)

            # 牛顿法更新：theta = theta - H^-1 g
            delta = np.linalg.solve(H, g)
            theta = theta - delta

            if np.linalg.norm(delta) < self.tolerance:
                break

        self.b, self.w = theta[0], theta[1:]
        return self

    def predict_proba(self, X):
        X = np.asarray(X, dtype=float)
        return self._sigmoid(X @ self.w + self.b)

    def predict(self, X, threshold=0.5):
        return (self.predict_proba(X) >= threshold).astype(int)

    def score(self, X, y):
        y = np.asarray(y).ravel()
        return float(np.mean(self.predict(X) == y))


class OneVsRestClassifier:
    """一对多（One-vs-Rest）多分类封装"""

    def __init__(self, base_estimator, **kwargs):
        self.base_estimator = base_estimator
        self.kwargs = kwargs
        self.models = {}
        self.classes_ = None

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y).ravel()
        self.classes_ = np.unique(y)
        for c in self.classes_:
            y_bin = (y == c).astype(int)
            model = self.base_estimator(**self.kwargs)
            model.fit(X, y_bin)
            self.models[c] = model
        return self

    def predict_proba(self, X):
        X = np.asarray(X, dtype=float)
        scores = np.column_stack([self.models[c].predict_proba(X) for c in self.classes_])
        return scores / scores.sum(axis=1, keepdims=True)

    def predict(self, X):
        proba = self.predict_proba(X)
        return self.classes_[np.argmax(proba, axis=1)]

    def score(self, X, y):
        return float(np.mean(self.predict(X) == np.asarray(y).ravel()))


if __name__ == "__main__":
    # 简单自测
    rng = np.random.default_rng(1)
    X = rng.standard_normal((200, 2))
    y = (X[:, 0] - X[:, 1] > 0).astype(int)

    model = LogisticRegressionNewton(n_iterations=100)
    model.fit(X, y)
    print("纯python代码2自测：准确率 =", round(model.score(X, y), 4))
    print("迭代轮数 =", len(model.loss_history))
    print("最终损失 =", round(model.loss_history[-1], 6))
