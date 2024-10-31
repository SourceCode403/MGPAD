import pickle
import random
import subprocess
import time
import mp_new_new
import read_xml_data as rxd
import numpy as np

CLOUD_NUM = 5
DATA_NUM = 8
cloud_list = []
results = []
base = 1
b = 1
c = 1


# 计算代价矩阵
cp = [14.03, 23.93, 8.02, 9.02, 10.12]
# 存储代价矩阵
sp = [0.002, 0.002, 0.004, 0.004, 0.004]
# 通信代价矩阵
# wp = [[0.02, 0.7, 0.7, 0.7, 0.7],
#         [0.8, 0.02, 0.8, 0.8, 0.8],
#         [0.012, 0.012, 0.002, 0.012, 0.012],
#         [0.015, 0.015, 0.015, 0.002, 0.015],
#         [0.02, 0.02, 0.02, 0.02, 0.002]]
# wp = [[base * 0.02, base * 0.7, base * 0.7, base * 0.7, base * 0.7],
#       [base * 0.8, base * 0.02, base * 0.8, base * 0.8, base * 0.8],
#       [base * 0.02, base * 0.02, base * 0.002, base * 0.02, base * 0.02],
#       [base * 0.04, base * 0.04, base * 0.04, base * 0.002, base * 0.04],
#       [base * 0.06, base * 0.06, base * 0.06, base * 0.06, base * 0.002]]
wp = [[base * 0.02, base * 0.7, base * 0.7, base * 0.7, base * 0.7, base * 0.7, base * 0.7, base * 0.7, base * 0.7],
      [base * 0.8, base * 0.02, base * 0.8, base * 0.8, base * 0.8, base * 0.8, base * 0.8, base * 0.8, base * 0.8],
      [base * 0.02, base * 0.02, base * 0.002, base * 0.02, base * 0.02, base * 0.02, base * 0.02, base * 0.02, base * 0.02],
      [base * 0.04, base * 0.04, base * 0.04, base * 0.002, base * 0.04, base * 0.04, base * 0.04, base * 0.04, base * 0.04],
      [base * 0.06, base * 0.06, base * 0.06, base * 0.06, base * 0.002, base * 0.06,  base * 0.06, base * 0.06, base * 0.06],
      [base * 0.06, base * 0.06, base * 0.06, base * 0.06, base * 0.06, base * 0.002, base * 0.06, base * 0.06, base * 0.06],
      [base * 0.06, base * 0.06, base * 0.06, base * 0.06, base * 0.06, base * 0.06, base * 0.002, base * 0.06, base * 0.06],
      [base * 0.06, base * 0.06, base * 0.06, base * 0.06, base * 0.06, base * 0.06, base * 0.06, base * 0.002, base * 0.06],
      [base * 0.06, base * 0.06, base * 0.06, base * 0.06, base * 0.06, base * 0.06, base * 0.06, base * 0.06, base * 0.002]]
# cpu和ram比例
g1 = 0.5
g2 = 0.5

class Workflow:

    def __init__(self):
        self.tasks = []  # 任务的节点集合
        self.edges = []  # 任务之间的数据依赖关系
        self.ddl = []  # 截止日期
        self.head_task = Task()  # 入任务
        self.end_task = Task()  # 出任务
        self.task_num = 0
        self.edge_num = 0
        self.traversal_task_list = []
        self.provider_list = []


class Task:

    def __init__(self):
        self.index = -1
        self.gt = -1
        self.scheduled = -1  # 调度
        self.size = 0    # 大小
        self.parent_list = []  # 父节点
        self.child_list = []  # 子节点
        self.out_degree = 0
        self.in_degree = 0
        self.wt = 0.0   # 计算成本
        self.ct = {}   # 通信成本
        self.sd = 0.0    # 子截止日期
        self.ss = None  # 执行时选择的对应服务实例
        self.final_position = -1  # 最后存放位置
        self.merge = 0
        self.merge_task = []
        self.partition = None
        self.gain = 0
        self.type = 0

    def __lt__(self, other):
        return self.gain < other.gain


class Edge:

    def __init__(self):
        self.head = Task()
        self.end = Task()
        self.sign = []
        self.cm_cost = 0.0     # 边的通信成本
        self.cm_cp_cost = 0.0  # 合并后的成本


class Cloud:

    def __init__(self):
        self.index = 0
        self.type = 0
        self.cpu = 0
        self.ram = 0
        self.speed = 0
        self.capacity_max = 0
        self.cp = 0
        self.sp = 0
        self.data_set = []


def custom_copy(origin_list):
    """
    使用pickle实现深拷贝,省时间
    :param origin_list:
    :return:
    """
    l = pickle.loads(pickle.dumps(origin_list))
    assert type(l) == type(origin_list)
    return l


def capacity_calculation(workflow):
    """
    计算每个混合云的容量
    :param workflow: 工作流
    :return:
    """
    total = 0
    for task in workflow.tasks:
        total += task.size
    capacity = total / 4
    return capacity


def calculate_total_cost(P, G, cloud_list):
    com_cost = 0
    sto_cost = 0
    cmp_cost = 0
    for t in G.traversal_task_list:
        x = P[t]
        cmp_cost += t.size / cloud_list[x].speed * cloud_list[x].cp
        sto_cost += t.size * cloud_list[x].sp
        if len(t.child_list) != 0:
            for c in t.child_list:
                if c not in P:
                    continue
                y = P[c]
                com_cost += wp[x][y] * t.size
    Tcost = com_cost + cmp_cost + sto_cost
    print(Tcost)
    return Tcost


def capacity_check(P, cloudlist):
    flag = 1
    capacity = [0, 0, 0, 0, 0]
    for key, value in P.items():
        capacity[value] += key.size
    print(capacity)
    for i in range(len(capacity)):
        if capacity[i] >= cloudlist[i].capacity_max:
            print("容量超出限制，不可解")
            flag = 0
    return flag


def assign_task_c_e(G):
    pos = [24, 30, 2, 13]
    # pos = random.sample(range(0, len(G.tasks)-1), 22)
    for i in pos:
        G.tasks[i].type = 1
        print(i)
        print(G.tasks[i])
    return G


if __name__ == '__main__':
    G = Workflow()

    cloud0 = Cloud()
    cloud0.index = 0
    cloud0.type = 0
    cloud0.cpu = 16
    cloud0.ram = 6
    cloud0.speed = g1 * cloud0.cpu + g2 * cloud0.ram
    cloud0.capacity_max = 300 * c
    cloud0.cp = 14.03 * b
    cloud0.sp = 0.002 * b
    cloud_list.append(cloud0)

    cloud1 = Cloud()
    cloud1.index = 1
    cloud1.type = 0
    cloud1.cpu = 24
    cloud1.ram = 8
    cloud1.speed = g1 * cloud1.cpu + g2 * cloud1.ram
    cloud1.capacity_max = 400 * c
    cloud1.cp = 23.93 * b
    cloud1.sp = 0.002 * b
    cloud_list.append(cloud1)

    cloud2 = Cloud()
    cloud2.index = 2
    cloud2.type = 1
    cloud2.cpu = 4
    cloud2.ram = 2
    cloud2.speed = g1 * cloud2.cpu + g2 * cloud2.ram
    cloud2.capacity_max = 180 * c
    cloud2.cp = 8.02 * b
    cloud2.sp = 0.004 * b
    cloud_list.append(cloud2)

    cloud3 = Cloud()
    cloud3.index = 3
    cloud3.type = 1
    cloud3.cpu = 4
    cloud3.ram = 4
    cloud3.speed = g1 * cloud3.cpu + g2 * cloud3.ram
    cloud3.capacity_max = 200 * c
    cloud3.cp = 9.02 * b
    cloud3.sp = 0.004 * b
    cloud_list.append(cloud3)

    cloud4 = Cloud()
    cloud4.index = 4
    cloud4.type = 1
    cloud4.cpu = 8
    cloud4.ram = 4
    cloud4.speed = g1 * cloud4.cpu + g2 * cloud4.ram
    cloud4.capacity_max = 200 * c
    cloud4.cp = 10.12 * b
    cloud4.sp = 0.004 * b
    cloud_list.append(cloud4)

    # cloud5 = Cloud()
    # cloud5.index = 5
    # cloud5.type = 1
    # cloud5.cpu = 8
    # cloud5.ram = 4
    # cloud5.speed = g1 * cloud4.cpu + g2 * cloud4.ram
    # cloud5.capacity_max = 200 * c
    # cloud5.cp = 10.12 * b
    # cloud5.sp = 0.004 * b
    # cloud_list.append(cloud5)
    #
    # cloud6 = Cloud()
    # cloud6.index = 6
    # cloud6.type = 1
    # cloud6.cpu = 8
    # cloud6.ram = 4
    # cloud6.speed = g1 * cloud4.cpu + g2 * cloud4.ram
    # cloud6.capacity_max = 200 * c
    # cloud6.cp = 10.12 * b
    # cloud6.sp = 0.004 * b
    # cloud_list.append(cloud6)
    #
    # cloud7 = Cloud()
    # cloud7.index = 7
    # cloud7.type = 1
    # cloud7.cpu = 8
    # cloud7.ram = 4
    # cloud7.speed = g1 * cloud4.cpu + g2 * cloud4.ram
    # cloud7.capacity_max = 200 * c
    # cloud7.cp = 10.12 * b
    # cloud7.sp = 0.004 * b
    # cloud_list.append(cloud7)

    # cloud8 = Cloud()
    # cloud8.index = 8
    # cloud8.type = 1
    # cloud8.cpu = 8
    # cloud8.ram = 4
    # cloud8.speed = g1 * cloud4.cpu + g2 * cloud4.ram
    # cloud8.capacity_max = 200 * c
    # cloud8.cp = 10.12 * b
    # cloud8.sp = 0.004 * b
    # cloud_list.append(cloud8)

    G = rxd.readData(G)
    G = assign_task_c_e(G)
    capacity_max = capacity_calculation(G)


    # mp_new_new
    start_time = time.time()
    P = mp_new_new.multilevel_partitioning(G, 5, cloud_list)
    print(P)
    for p in P:
        print(p.index, P[p])
    flag = capacity_check(P, cloud_list)
    T = calculate_total_cost(P, G, cloud_list)
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"算法执行时间：{execution_time}秒")









