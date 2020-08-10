import rubik


def bfs_level(frontier, parents, func):
    """
    Move 1 level forward in BFS.
    """
    next = []
    for position in frontier:
        for move in rubik.quarter_twists:
            next_position = rubik.perm_apply(func(move), position)
            if next_position not in parents:
                parents[next_position] = (move, position)
                next.append(next_position)
    return next


def construct_path(position, forward_parents, backward_parents):
    """
    Construct the path from the graph.
    """
    path = []
    vertex = position
    while forward_parents[vertex]:
        move, vertex = forward_parents[vertex]
        path.append(move)
    path.reverse()

    vertex = position
    while backward_parents[vertex]:
        move, vertex = backward_parents[vertex]
        path.append(move)
    return path


def shortest_path(start, end):
    """
    Using 2-way BFS, finds the shortest path from start_position to
    end_position. Returns a list of moves. 

    You can use the rubik.quarter_twists move set.
    Each move can be applied using rubik.perm_apply
    """
    if start == end:
        return []
    
    forward_parents, backward_parents = { start: None }, { end: None }
    forward_frontier, backward_frontier = [start], [end]
    
    for i in range(7):
        forward_frontier = bfs_level(forward_frontier, forward_parents, lambda x: x)
        for position in forward_frontier:
            if position in backward_parents:
                return construct_path(position, forward_parents, backward_parents)
        
        backward_frontier = bfs_level(backward_frontier, backward_parents, rubik.perm_inverse)
        for position in backward_frontier:
            if position in forward_parents:
                return construct_path(position, forward_parents, backward_parents)
