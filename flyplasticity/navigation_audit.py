"""Anatomical reachability only: contacts never imply functional transmission."""
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import breadth_first_order


def contact_graph(n, pre, post, contacts):
    pre, post, contacts = map(np.asarray, (pre, post, contacts))
    if (pre.ndim != 1 or pre.shape != post.shape or pre.shape != contacts.shape
            or not np.isfinite(contacts).all() or np.any(contacts <= 0)
            or np.any(contacts != np.floor(contacts))
            or pre.dtype.kind not in 'iu' or post.dtype.kind not in 'iu'
            or np.any(pre < 0) or np.any(post < 0)
            or np.any(pre >= n) or np.any(post >= n)):
        raise ValueError('Invalid anatomical contacts')
    return csr_matrix((contacts.astype(np.int64), (pre, post)), shape=(n, n))


def shortest_paths(graph, source, targets):
    """One directed shortest witness per target, not a strength-ranked pathway."""
    _, parent = breadth_first_order(graph, source, directed=True)
    result = {}
    for target in targets:
        path = [int(target)]
        while path[-1] != source and parent[path[-1]] >= 0:
            path.append(int(parent[path[-1]]))
        result[int(target)] = path[::-1] if path[-1] == source else None
    return result


def input_coverage(graph, selected):
    selected = np.asarray(selected, dtype=int)
    total = int(graph[:, selected].sum())
    internal = int(graph[selected][:, selected].sum())
    return dict(total_contacts=total, internal_contacts=internal,
                excluded_contacts=total-internal,
                retained_fraction=internal/total if total else None)
