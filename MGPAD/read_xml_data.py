import queue
import main
import numpy
from xml.etree import ElementTree as ET


def readData(G):
    # print("进入xml")
    task_list = []
    edge_list = []
    tree = ET.parse('Montage_50.xml')
    root = tree.getroot()

    for job in root.iterfind("job"):
        # print(job.get("id"))
        t = main.Task()
        t.index = int(job.get("id")[2:])
        for uses in job.findall("uses"):
            t.size += (int(uses.get("size")) / 1024 / 1024)
        task_list.append(t)
    G.tasks = task_list
    G.task_num = len(task_list)

    for child in root.iterfind("child"):
        index = int(child.get("ref")[2:])
        task_c = task_list[index]
        for parent in child.findall("parent"):
            index = int(parent.get("ref")[2:])
            task_p = task_list[index]

            task_c.parent_list.append(task_p)
            task_p.child_list.append(task_c)

            e = main.Edge()
            e.head = task_p
            e.end = task_c
            edge_list.append(e)
    G.edges = edge_list
    G.edge_num = len(edge_list)

    for task in task_list:
        # print(task.index)
        task.out_degree = (len(task.child_list))
        # print("出度", task.out_degree)
        task.in_degree = (len(task.parent_list))
        # print("入度", task.in_degree)

    for t1 in task_list:
        if len(t1.parent_list) == 0:
            G.head_task.child_list.append(t1)
        if len(t1.child_list) == 0:
            G.end_task.parent_list.append(t1)
    q = queue.Queue()
    q.put(G.head_task)
    traversal_task_list = G.traversal_task_list
    while not q.empty():
        t2 = q.get()
        if t2.index != -1:
            traversal_task_list.append(t2)
        for task1 in t2.child_list:
            flag = True
            for p1 in task1.parent_list:
                if p1 not in traversal_task_list:
                    flag = False
                    continue
            if flag:
                q.put(task1)

    return G
