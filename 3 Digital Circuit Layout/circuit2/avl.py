import bst


class AVLNode(bst.BSTNode):
    """A node in an AVL."""

    def __init__(self, key):
        """Creates a node that will be inserted in an AVL.

        See __init__ in BSTNode."""
        bst.BSTNode.__init__(self, key)
        self.height = 0

    def update_subtree_info(self):
        """Updates pre-computed fields such as the node's subtree height."""
        self.height = self._uncached_height()

    def _uncached_height(self):
        """Re-computes the node's height based on the children's heights."""
        return 1 + max((self.left and self.left.height) or -1,
                       (self.right and self.right.height) or -1)


class AVL(bst.BST):
    """AVL binary search tree implementation.

    All queries and updates are guaranteed to take O(lg N) time.
    """

    def __init__(self, node_class=AVLNode):
        """Creates an empty AVL tree.

        Args:
          node_class (optional): the class of nodes in the tree, defaults to AVLNode
        """
        bst.BST.__init__(self, node_class)

    def insert(self, key):
        """Inserts a node into the subtree rooted at this node.

        Args:
          key: the key of the node to be inserted

        Returns an AVLNode with the given key that belongs to this tree.
        """
        inserted_node = bst.BST.insert(self, key)
        self._rebalance(inserted_node)
        return inserted_node

    def delete(self, key):
        """Removes the node with the given key from this BST.

        Args:
          key: the key of the node to be deleted

        Returns a BSTNode instance with the given key, which was removed from the
        tree. If this tree does not contain the given key, returns None. The deleted
        node's fields will still be set, despite the fact that it does not belong to
        the tree anymore.
        """
        deleted_node = bst.BST.delete(self, key)
        # NOTE: deleted_node still has its parent set, and it happens to be the
        #       first potentially out-of-balance node.
        self._rebalance(deleted_node.parent)
        return deleted_node

    def _rebalance(self, node):
        while node is not None:
            # NOTE: rebalance is called after an insertion or a deletion; asides from
            #       fixing the imbalance, it is also responsible for updating the
            #       cached sub-tree information in each node on the path to the root
            node.update_subtree_info()

            if AVL._height(node.left) >= 2 + AVL._height(node.right):
                if AVL._height(node.left.left) < AVL._height(node.left.right):
                    self._left_rotate(node.left)
                self._right_rotate(node)
            elif AVL._height(node.right) >= 2 + AVL._height(node.left):
                if AVL._height(node.right.right) < AVL._height(node.right.left):
                    self._right_rotate(node.right)
                self._left_rotate(node)
            node = node.parent

    @staticmethod
    def _height(node):
        if node is not None:
            return node.height
        else:
            return -1

    def _left_rotate(self, x):
        y = x.right
        y.parent = x.parent
        if y.parent is None:
            self.root = y
        else:
            if y.parent.left is x:
                y.parent.left = y
            else:  # y.parent.right is x
                y.parent.right = y
        x.right = y.left
        if x.right is not None:
            x.right.parent = x
        y.left = x
        x.parent = y
        x.update_subtree_info()
        y.update_subtree_info()

    def _right_rotate(self, x):
        y = x.left
        y.parent = x.parent
        if y.parent is None:
            self.root = y
        else:
            if y.parent.left is x:
                y.parent.left = y
            else:  # y.parent.right is x
                y.parent.right = y
        x.left = y.right
        if x.left is not None:
            x.left.parent = x
        y.right = x
        x.parent = y
        x.update_subtree_info()
        y.update_subtree_info()
