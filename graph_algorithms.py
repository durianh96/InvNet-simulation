def find_preds_of_node(edges: list):
    """
    Find the predecessors of each node in a directed graph.
    Args:
        edges:

    Returns:

    """
    nodes = set([node for tu in edges for node in tu])
    preds_of_node = {node: set() for node in nodes}
    for pred, succ in edges:
        preds_of_node[succ].add(pred)
    return preds_of_node


def find_succs_of_node(edges: list):
    """
    Find the successors of each node in a directed graph.
    Args:
        edges:

    Returns:

    """
    nodes = set([node for tu in edges for node in tu])
    succs_of_node = {node: set() for node in nodes}
    for pred, succ in edges:
        succs_of_node[pred].add(succ)
    return succs_of_node


def cal_lt_of_node(edges: list, process_lt_of_node: dict, lt_of_edge: dict):
    nodes = set([node for tu in edges for node in tu])
    preds_of_node = find_preds_of_node(edges)
    lt_of_node = {node: process_lt for node, process_lt in process_lt_of_node.items()}
    for node in nodes:
        if len(preds_of_node[node]) > 0:
            lt_of_node[node] += max([lt_of_edge[(pred, node)] for pred in preds_of_node[node]])
    return lt_of_node
