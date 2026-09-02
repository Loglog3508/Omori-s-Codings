class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class StudentLinkedList:
    def __init__(self):
        self.head = None
        self.length = 0

    def append(self, name):
        new_node = Node(name)
        if not self.head:
            self.head = new_node
        else:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = new_node
        self.length += 1

    def display(self):
        if not self.head:
            print("班级暂无学生")
            return
        cur = self.head
        pos = 1
        while cur:
            print(f"{pos}. {cur.data}")
            cur = cur.next
            pos += 1
        print(f"班级总人数：{self.length}")

    def search(self, name):
        cur = self.head
        pos = 1
        while cur:
            if cur.data == name:
                print(f"{name} 在表中的位置（学号）：{pos}")
                return pos
            cur = cur.next
            pos += 1
        print("未找到，请重新输入待查人姓名：")
        return -1

    def insert_after(self, target, new_name):
        cur = self.head
        while cur:
            if cur.data == target:
                new_node = Node(new_name)
                new_node.next = cur.next
                cur.next = new_node
                self.length += 1
                return True
            cur = cur.next
        print(f"未找到学生 {target}，无法插入")
        return False

    def delete(self, name):
        if not self.head:
            print("链表为空，无学生可删除")
            return False
        if self.head.data == name:
            self.head = self.head.next
            self.length -= 1
            return True
        prev = self.head
        cur = self.head.next
        while cur:
            if cur.data == name:
                prev.next = cur.next
                self.length -= 1
                return True
            prev = cur
            cur = cur.next
        print(f"未找到学生 {name}，无法删除")
        return False

if __name__ == "__main__":
    sll = StudentLinkedList()
    print("=== 建立学生姓名信息单链表（尾插法） ===")
    # 初始化学生（可自行修改）
    init_names = ["洪翼雄", "张三","李四", "王五", "赵六"]
    for name in init_names:
        sll.append(name)

    print("\n=== 初始班级信息 ===")
    sll.display()

    while True:
        search_name = input("\n请输入要查找的学生姓名（输入q退出）：")
        if search_name.lower() == "q":
            break
        if sll.search(search_name) != -1:
            break

    target = input("\n请输入要在其后插入新生的学生姓名：")
    new_stu = input("请输入新生姓名：")
    if sll.insert_after(target, new_stu):
        print(f"\n=== 插入新生{new_stu}后班级信息： ===")
        sll.display()

    del_name = input("\n请输入要删除的学生姓名：")
    if sll.delete(del_name):
        print(f"\n=== 删除{del_name}后班级信息： ===")
        sll.display()