# 定义二叉树节点
class TreeNode:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None


# 1. 建立二叉树（按先序序列，None 表示空节点）
def build_tree(preorder):
    def helper(it):
        val = next(it)
        if val is None:
            return None
        node = TreeNode(val)
        node.left = helper(it)
        node.right = helper(it)
        return node
    return helper(iter(preorder))


# 2. 递归遍历
def preorder_recursive(root, res=None):
    if res is None:
        res = []
    if root:
        res.append(root.val)
        preorder_recursive(root.left, res)
        preorder_recursive(root.right, res)
    return res


def inorder_recursive(root, res=None):
    if res is None:
        res = []
    if root:
        inorder_recursive(root.left, res)
        res.append(root.val)
        inorder_recursive(root.right, res)
    return res


def postorder_recursive(root, res=None):
    if res is None:
        res = []
    if root:
        postorder_recursive(root.left, res)
        postorder_recursive(root.right, res)
        res.append(root.val)
    return res


# 3. 非递归遍历
def preorder_non_recursive(root):
    res = []
    stack = [root]
    while stack:
        node = stack.pop()
        if node:
            res.append(node.val)
            # 先压右再压左，保证出栈顺序是先左后右
            stack.append(node.right)
            stack.append(node.left)
    return res


def inorder_non_recursive(root):
    res = []
    stack = []
    cur = root
    while cur or stack:
        while cur:
            stack.append(cur)
            cur = cur.left
        cur = stack.pop()
        res.append(cur.val)
        cur = cur.right
    return res


# 4. 求叶子节点个数（递归）
def count_leaves(root):
    if not root:
        return 0
    if not root.left and not root.right:
        return 1
    return count_leaves(root.left) + count_leaves(root.right)


# ---------- 测试运行 ----------
if __name__ == "__main__":
    # 示例先序序列，None 代表空
    pre = [1, 2, 4, None, None, 5, None, None, 3, None, 6, None, None]
    root = build_tree(pre)

    print("递归先序遍历:", preorder_recursive(root))
    print("递归中序遍历:", inorder_recursive(root))
    print("递归后序遍历:", postorder_recursive(root))
    print("非递归先序遍历:", preorder_non_recursive(root))
    print("非递归中序遍历:", inorder_non_recursive(root))
    print("叶子节点个数:", count_leaves(root))