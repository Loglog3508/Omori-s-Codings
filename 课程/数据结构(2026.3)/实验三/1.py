# -*- coding: utf-8 -*-
# 查找算法实验：二分查找 + 二叉排序树查找

# ===================== 1. 二分查找 =====================
def binary_search(arr, target):
    """
    二分查找（必须有序数组）
    :param arr: 有序列表
    :param target: 要查找的关键字
    :return: 找到返回索引，未找到返回-1
    """
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            print(f"[二分查找] 找到关键字 {target}，位置索引：{mid}")
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    print(f"[二分查找] 未找到关键字 {target}")
    return -1


# ===================== 2. 二叉排序树 BST =====================
class TreeNode:
    """二叉树节点"""
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None

class BST:
    """二叉排序树类"""
    def __init__(self):
        self.root = None

    def insert(self, val):
        """插入节点"""
        if not self.root:
            self.root = TreeNode(val)
            return
        curr = self.root
        while True:
            if val < curr.val:
                if not curr.left:
                    curr.left = TreeNode(val)
                    break
                curr = curr.left
            elif val > curr.val:
                if not curr.right:
                    curr.right = TreeNode(val)
                    break
                curr = curr.right
            else:
                print(f"[BST] 关键字 {val} 已存在，跳过插入")
                break

    def search(self, val):
        """查找节点"""
        curr = self.root
        while curr:
            if val == curr.val:
                print(f"[BST查找] 找到关键字 {val}")
                return True
            elif val < curr.val:
                curr = curr.left
            else:
                curr = curr.right
        print(f"[BST查找] 未找到关键字 {val}")
        return False

    def delete(self, val):
        """删除节点"""
        parent = None
        curr = self.root
        # 查找节点
        while curr and curr.val != val:
            parent = curr
            curr = curr.left if val < curr.val else curr.right
        if not curr:
            print(f"[BST删除] 未找到关键字 {val}，删除失败")
            return False

        # 情况1：无左孩子
        if not curr.left:
            if not parent:
                self.root = curr.right
            elif parent.left == curr:
                parent.left = curr.right
            else:
                parent.right = curr.right
        # 情况2：无右孩子
        elif not curr.right:
            if not parent:
                self.root = curr.left
            elif parent.left == curr:
                parent.left = curr.left
            else:
                parent.right = curr.left
        # 情况3：双孩子
        else:
            succ_parent, succ = curr, curr.right
            while succ.left:
                succ_parent, succ = succ, succ.left
            curr.val = succ.val
            if succ_parent == curr:
                succ_parent.right = succ.right
            else:
                succ_parent.left = succ.right
        print(f"[BST删除] 关键字 {val} 删除成功")
        return True


# ===================== 主函数：测试 =====================
if __name__ == "__main__":
    print("====== 查找算法实验开始 ======\n")

    # 测试二分查找
    print("--- 二分查找测试 ---")
    sorted_arr = [1, 3, 5, 7, 9, 11, 13, 15]
    binary_search(sorted_arr, 7)
    binary_search(sorted_arr, 8)

    print("\n------------------------\n")

    # 测试二叉排序树
    print("--- 二叉排序树 BST 测试 ---")
    bst = BST()
    # 插入数据建立树
    data = [5, 3, 7, 2, 4, 6, 8]
    for num in data:
        bst.insert(num)

    # 查找
    bst.search(4)
    bst.search(9)

    # 删除
    bst.delete(7)
    bst.search(7)

    print("\n====== 实验结束 ======")