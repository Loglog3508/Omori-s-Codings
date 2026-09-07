"""
实验一 纯python代码1：使用梯度下降法从零实现逻辑回归（Logistic Regression）

仅使用 numpy 实现，不依赖 sklearn 等机器学习框架。
原理：
    z = w^T x + b
    ŷ = sigmoid(z) = 1 / (1 + exp(-z))
    损失函数（交叉熵）：
        J(w, b) = -(1/m) * Σ [y·ln(ŷ) + (1-y)·ln(1-ŷ)]
    梯度：
        ∂J/∂w = (1/m) * X^T (ŷ - y)
        ∂J/∂b = (1/m) * Σ (ŷ - y)
    使用批量梯度下降迭代更新参数。
"""
import numpy as np


class LogisticRegressionGD:
    """基于批量梯度下降的逻辑回归（二分类）"""

    def __init__(self, learning_rate=0.05, n_iterations=2000, tolerance=1e-6, random_state=42):
        self.learning_rate = learning_rate        # 学习率
        self.n_iterations = n_iterations          # 最大迭代次数
        self.tolerance = tolerance                # 损失变化阈值（提前停止）
        self.random_state = random_state
        self.w = None                             # 特征权重
        self.b = None                             # 偏置
        self.loss_history = []                    # 每轮损失，用于绘制收敛曲线

    def _sigmoid(self, z):
        """数值稳定的 sigmoid 函数"""
        z = np.clip(z, -500, 500)
        return 1.0 / (1.0 + np.exp(-z))

    def fit(self, X, y):
        """训练模型：X 为 (m, n) 特征矩阵，y 为 (m,) 的 0/1 标签"""
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float).ravel()
        m, n = X.shape

        rng = np.random.default_rng(self.random_state)
        self.w = rng.standard_normal(n) * 0.01
        self.b = 0.0

        for i in range(self.n_iterations):
            # 前向传播
            z = X @ self.w + self.b
            y_hat = self._sigmoid(z)

            # 交叉熵损失
            loss = -np.mean(y * np.log(y_hat + 1e-12) + (1 - y) * np.log(1 - y_hat + 1e-12))
            self.loss_history.append(loss)

            # 梯度
            error = y_hat - y
            dw = (1.0 / m) * (X.T @ error)
            db = (1.0 / m) * np.sum(error)

            # 参数更新
            self.w -= self.learning_rate * dw
            self.b -= self.learning_rate * db

            # 损失收敛则提前停止
            if i > 0 and abs(self.loss_history[-2] - loss) < self.tolerance:
                break
        return self

    def predict_proba(self, X):
        """返回样本属于正类的概率"""
        X = np.asarray(X, dtype=float)
        return self._sigmoid(X @ self.w + self.b)

    def predict(self, X, threshold=0.5):
        """返回 0/1 类别预测"""
        return (self.predict_proba(X) >= threshold).astype(int)

    def score(self, X, y):
        """分类准确率"""
        y = np.asarray(y).ravel()
        return float(np.mean(self.predict(X) == y))


class OneVsRestClassifier:
    """一对多（One-vs-Rest）多分类封装，将多分类任务拆成多个二分类"""

    def __init__(self, base_estimator, **kwargs):
        self.base_estimator = base_estimator
        self.kwargs = kwargs
        self.models = {}     # 每个类别对应的二分类器
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
        # 归一化为概率
        return scores / scores.sum(axis=1, keepdims=True)

    def predict(self, X):
        proba = self.predict_proba(X)
        return self.classes_[np.argmax(proba, axis=1)]

    def score(self, X, y):
        return float(np.mean(self.predict(X) == np.asarray(y).ravel()))


if __name__ == "__main__":
    # 简单自测：在随机生成的线性可分数据上验证
    rng = np.random.default_rng(0)
    X = rng.standard_normal((200, 2))
    y = (X[:, 0] + 2 * X[:, 1] > 0).astype(int)

    model = LogisticRegressionGD(learning_rate=0.5, n_iterations=500)
    model.fit(X, y)
    print("纯python代码1自测：准确率 =", round(model.score(X, y), 4))
    print("最终损失 =", round(model.loss_history[-1], 6))
