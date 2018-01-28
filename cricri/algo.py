"""
A collection of functions to perform operation on containers.
"""


from collections import defaultdict


def find_loop(graph):
    """
    Find loop in *graph*
    """

    loops_from_start = defaultdict(list)

    def _walk(graph, start, end, visited_nodes, path):
        """
        Find all pathes between *start* and *end* through *graph*.
        without visit the same node.

        The pathes are stored in *loops_from_start*.
        """
        for next_node in graph[start]:
            if next_node == end:
                loops_from_start[end].append(
                    (end,) + path + (next_node,)
                )
            elif next_node not in visited_nodes:
                _walk(graph, next_node, end,
                      visited_nodes | {next_node, },
                      path + (next_node,))

    for node in graph:
        _walk(graph, node, node, set(), tuple())

    return loops_from_start


def insert_loop(pathes, loops_from_start):
    """
    Insert loop in list of path.
    """
    pathes_with_loop = []
    for path in pathes:
        path_with_loop = [()]
        for node in path:
            path_with_loop = [
                out + loop
                for out in path_with_loop
                for loop in loops_from_start[node]]

        pathes_with_loop.extend(path_with_loop)

    return pathes_with_loop


def all_longer_path(graph, start, path, sub_path_explored, out):
    """
    Find all longer pathes through graph.

    graph - must be a dict mappinp graph node to next graph node.
    start - must be a first graph node
    path - must be an empty list
    sub_path_explored - must be an empty set
    out - path found is added to out list.
    """
    flag = True
    for step in graph[start]:
        sub_path = (start, step)
        if sub_path not in sub_path_explored:
            flag = False
            all_longer_path(graph, step,
                            path + [sub_path],
                            sub_path_explored | {sub_path},
                            out)
    if flag:
        if len(graph) == 1:
            out.append((start,))
        else:
            out.append(tuple(e[0] for e in path) + (path[-1][-1],))


def walk(graph, start, nb_loop=0):
    """
    Find all longer pathes through graph.

    graph - must be a dict mappinp graph node to next graph node.
    start - must be a first graph node
    nb_loop - number of loops per node
    """

    if nb_loop < 0:
        raise ValueError('last parameter must be greater or equal 0')

    longer_pathes = []
    all_longer_path(graph, start, [], set(), longer_pathes)

    if nb_loop:
        loops_from_start = find_loop(graph)
        loops_from_start = {
            start: [(loop + loop[1:] * (nb_loop - 1))
                    for loop
                    in loops]
            for start, loops
            in loops_from_start.items()
        }

        for node in graph:
            loops_from_start.setdefault(node, [(node,)])
        longer_pathes = insert_loop(longer_pathes, loops_from_start)

    return longer_pathes
