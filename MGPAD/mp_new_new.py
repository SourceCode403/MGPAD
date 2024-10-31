import main
import numpy as np
import random


M = {}


def multilevel_partitioning(G, k, cloud_list):

    H = [G]
    while len(H[-1].tasks) > k:
        G_c, mc = coarsen(H[-1], cloud_list)
        if mc == 1:
            break
        H.append(G_c)
        print(len(H[-1].tasks))
    P = initial_partition(H[-1], k, cloud_list)
    while len(H) > 0:
        P_project = project(P, H[-1])
        P = refine(P_project, H[-1], k, cloud_list)
        H.pop()

    return P


def coarsen(G, cloud_list):

    global M
    mc = 0
    E_m = match(G)
    G_c = main.Workflow()
    for e_m in E_m:
        u, v = e_m.head, e_m.end
        size = u.size + v.size
        capacity_min = min(cloud_list, key=lambda cloud: cloud.capacity_max).capacity_max
        if size < capacity_min:
            w = main.Task()
            w.merge = 1
            w.merge_task.append((u, v))
            M[u] = w
            M[v] = w
            w.size = u.size + v.size
            w.parent_list = list(set(u.parent_list) | set(v.parent_list))
            w.child_list = list(set(u.child_list) | set(v.child_list))
        else:
            mc = 1

    for u in G.tasks:
        if u not in M:
            G_c.tasks.append(u)
        else:
            w = M[u]
            if w not in G_c.tasks:
                G_c.tasks.append(w)

    for e in G.edges:
        u, v = e.head, e.end
        e.cm_cost = main.wp[u.final_position][v.final_position] * u.size
        if u not in M and v not in M:
            e_c = main.Edge()
            e_c.head, e_c.end = u, v
            G_c.edges.append(e_c)
            e_c.cm_cost = e.cm_cost
            print(u, v)
            if e_c.end not in e_c.head.child_list:
                e_c.head.child_list.append(e_c.end)
            if e_c.head not in e_c.end.parent_list:
                e_c.end.parent_list.append(e_c.head)
        elif u in M and v in M and M[u] == M[v]:
            continue
        else:
            w_u = M[u] if u in M else u
            w_v = M[v] if v in M else v
            flag = 0
            for w_u_v in G_c.edges:
                if w_u_v.head == w_u and w_u_v.end == w_v:
                    w_u_v.cm_cost += e.cm_cost
                    flag = 1
            if not flag:
                e_w = main.Edge()
                e_w.head = w_u
                e_w.end = w_v
                G_c.edges.append(e_w)
                e_w.cm_cost += e.cm_cost
                if e_w.end not in e_w.head.child_list:
                    e_w.head.child_list.append(e_w.end)
                if e_w.head not in e_w.end.parent_list:
                    e_w.end.parent_list.append(e_w.head)

    return G_c, mc


def match(G):

    E_m = set()
    N_m = set()
    E = list(G.edges)
    for e in G.edges:
        e.cm_cost = main.wp[e.head.final_position][e.end.final_position] * e.head.size
    W = [e.cm_cost for e in E]
    probabilities = [w / sum(W) for w in W]
    E_w = sorted(E, key=lambda x: probabilities[E.index(x)], reverse=True)
    for e_w in E_w:
        u, v = e_w.head, e_w.end
        if u not in N_m and v not in N_m:
            E_m.add(e_w)
            N_m.add(u)
            N_m.add(v)

    return E_m


def initial_partition(G, k, cloud_list):

    P = {}
    capacity = [0] * k
    nodes = list(G.tasks)
    nodes.sort(key=lambda u: u.size, reverse=True)
    for node in nodes:
        c_min = float('inf')
        current_part = -1
        if node.type == 0:
            for i in range(len(cloud_list)):
                c = node.size / cloud_list[i].speed * cloud_list[i].cp + node.size * cloud_list[i].sp
                if capacity[i] + node.size < cloud_list[i].capacity_max:
                    if c < c_min:
                        c_min = c
                        current_part = i
                else:
                    continue
        if node.type == 1:
            for i in range(len(cloud_list)):
                if cloud_list[i].type == 0:
                    continue
                if cloud_list[i].type == 1:
                    c = node.size / cloud_list[i].speed * cloud_list[i].cp + node.size * cloud_list[i].sp
                    if capacity[i] + node.size < cloud_list[i].capacity_max:
                        if c < c_min:
                            c_min = c
                            current_part = i
                    else:
                        continue
        capacity[current_part] += node.size
        P[node] = current_part
    print("COST", P)

    return P


def project(P, G):

    P_p = {}
    for u in G.tasks:
        if u in P:
            P_p[u] = P[u]
        else:
            if u in M:
                v = M[u]
                while v not in P:
                    v = M[v]
                P_p[u] = P[v]

    return P_p


def refine(P, G, k, cloud_list):

    capacity = [0] * k
    for node in G.tasks:
        capacity[P[node]] += node.size

    for task in G.tasks:
        subset = P[task]
        best_subset = subset
        best_gain = 0
        for e in G.edges:
            gain = 0
            if e.head == task:
                t = e.end
                gain = D(task, t, P)
                cs_gain = calculate_cmp_gain(task, t, P, cloud_list)
                gain = gain + cs_gain
            if e.end == task:
                t = e.head
                gain = D(t, task, P)
                cs_gain = calculate_cmp_gain(t, task, P, cloud_list)
                gain = gain + cs_gain
            if gain > best_gain:
                flag = capacity_check(P, capacity, cloud_list, task, t)
                if flag == 1:
                    if (task.type == 1 and P[t].type == 0) or (t.type == 1 and P[task].type == 0):
                        continue
                    else:
                        best_subset = P[t]
                        best_gain = gain
            if best_subset != subset:
                P[task] = best_subset
                capacity[subset] -= task.size
                capacity[best_subset] += task.size
                capacity[best_subset] -= t.size
                capacity[subset] += t.size
            else:
                break

    return P


def D(a, b, P):

    a_external_cost = 0
    a_internal_cost = 0
    b_external_cost = 0
    b_internal_cost = 0
    # 遍历所有的节点
    for b1 in P:
        if P[b1] == P[b]:
            a_external_cost += main.wp[P[a]][P[b1]] * a.size
    for a1 in P:
        if P[a1] == P[a]:
            if a1 != a:
                a_internal_cost += main.wp[P[a]][P[a1]] * a.size
    a_d_cost = a_external_cost - a_internal_cost
    for a2 in P:
        if P[a2] == P[b]:
            b_external_cost += main.wp[P[b]][P[a2]] * b.size
    for b2 in P:
        if P[b2] == P[b]:
            if b2 != b:
                b_internal_cost += main.wp[P[b]][P[b2]] * b.size
    b_d_cost = b_external_cost - b_internal_cost
    ab_cost = main.wp[P[a]][P[b]] * a.size
    g_cost = a_d_cost + b_d_cost - 2 * ab_cost

    return g_cost


def calculate_cmp_gain(a, b, P, cloud_list):

    a_cmp_cost = a.size / cloud_list[P[a]].speed * cloud_list[P[a]].cp - a.size / cloud_list[P[b]].speed * cloud_list[P[b]].cp
    b_cmp_cost = b.size / cloud_list[P[b]].speed * cloud_list[P[b]].cp - b.size / cloud_list[P[a]].speed * cloud_list[P[a]].cp
    a_sto_cost = a.size * cloud_list[P[a]].sp - a.size * cloud_list[P[b]].sp
    b_sto_cost = b.size * cloud_list[P[b]].sp - b.size * cloud_list[P[a]].sp
    cs_gain = a_cmp_cost + b_cmp_cost + a_sto_cost + b_sto_cost

    return cs_gain


def find_best_partition(G, k, capacity_max, num_iterations, cloud_list):

    best_cost = float('inf')
    best_partition = None

    for _ in range(num_iterations):
        partition, cost = initial_partition(G, k, capacity_max, cloud_list)

        if cost < best_cost:
            best_cost = cost
            best_partition = partition

    return best_partition, best_cost


def capacity_check(P: object, capacity: object, cloud_list: object, node: object, t: object) -> object:

    check = 1
    capacity[P[node]] -= node.size
    capacity[P[t]] += node.size
    capacity[P[t]] -= t.size
    capacity[P[node]] += t.size
    for i in range(len(capacity)):
        if capacity[i] >= cloud_list[i].capacity_max or capacity[i] <= 0:
            check = 0

    return check




