class BSTNode(object):
    """A node in a vanilla BST tree."""

    def __init__(self, key):
        """Creates a node that will be inserted in a BST.

        After the node is created, it should be inserted in a tree by calling
        BST.insert(). Until that happens, the node is not in a valid state.

        Args:
            key: the key associated with the node
        """
        self.key = key
        self.parent = None
        self.left = None
        self.right = None

    def find(self, key):
        """The node with the given key in the subtree rooted at this node.

        Args:
            key: the key of the node to be returned

        Returns a BSTNode instance with the given key, or None if the key was not
        found.
        """
        if key < self.key:
            return self.left and self.left.find(key)
        elif key > self.key:
            return self.right and self.right.find(key)
        return self

    def min(self):
        """The node with the minimum key in the subtree rooted at this node.

        Returns a BSTNode instance with the minimum key.
        """
        if self.left is None:
            return self
        return self.left.min()

    def successor(self):
        """The node with the next larger key (the successor) in the BST.

        Returns a BSTNode instance, or None if this node has no successor.
        """
        if self.right is not None:
            return self.right.min()
        current = self
        while current.parent is not None and current is current.parent.right:
            current = current.parent
        return current.parent

    def insert(self, node):
        """Inserts a node into the subtree rooted at this node.

        Args:
            node: the node to be inserted

        Returns the node argument, if the node was inserted in the tree. If a node
        with the same key was found, that node is returned instead.
        """
        if node.key < self.key:
            if self.left is not None:
                return self.left.insert(node)
            node.parent = self
            self.left = node
            return node
        elif node.key > self.key:
            if self.right is not None:
                return self.right.insert(node)
            node.parent = self
            self.right = node
            return node
        return self

    def delete(self):
        """Deletes this node from the BST.

        Returns the deleted BSTNode instance. The instance might be different from
        this node, but will have this node's key. The deleted node's fields will
        still be set, despite the fact that it does not belong to the tree anymore.
        """
        if self.left is None or self.right is None:
            if self is self.parent.left:
                self.parent.left = self.left or self.right
                if self.parent.left is not None:
                    self.parent.left.parent = self.parent
            else:
                self.parent.right = self.left or self.right
                if self.parent.right is not None:
                    self.parent.right.parent = self.parent
            return self
        else:
            s = self.successor()
            # NOTE: deleting before swapping the keys so the BST RI is never violated.
            deleted_node = s.delete()
            self.key, s.key = s.key, self.key
            return deleted_node


class BST(object):
    """A binary search tree."""

    def __init__(self, node_class=BSTNode):
        """Creates an empty BST.

        Args:
            node_class (optional): the class of nodes in the tree, defaults to BSTNode
        """
        self.node_class = node_class
        self.root = None

    def find(self, key):
        """The node with the given key in this BST.

        Args:
            key: the key of the node to be returned

        Returns a BSTNode instance with the given key, or None if the key was not
        found.
        """
        return self.root and self.root.find(key)

    def min(self):
        """The node with the minimum key in this BST."""
        if self.root is None:
            return None
        else:
            return self.root.min()

    def insert(self, key):
        """Inserts a node into the subtree rooted at this node.

        Args:
            key: the key of the node to be inserted

        Returns a BSTNode with the given key that belongs to this tree.
        """
        node = self.node_class(key)
        if self.root is None:
            self.root = node
            return node
        return self.root.insert(node)

    def delete(self, key):
        """Removes the node with the given key from this BST.

        Args:
            key: the key of the node to be deleted

        Returns a BSTNode instance with the given key, which was removed from the
        tree. If this tree does not contain the given key, returns None. The deleted
        node's fields will still be set, despite the fact that it does not belong to
        the tree anymore.
        """
        node = self.find(key)
        if node is None:
            return None
        if node is self.root:
            pseudo_root = self.node_class(None)
            pseudo_root.left = self.root
            self.root.parent = pseudo_root
            deleted_node = self.root.delete()
            self.root = pseudo_root.left
            if self.root is not None:
                self.root.parent = None
            return deleted_node
        else:
            return node.delete()

    def successor(self, key):
        """Returns the node that contains the next larger (the successor) key in
        the BST in relation to the node with key k.

        Args:
            key: the key of the node whose successor will be returned

        Returns a BSTNode instance whose key is the successor of the given key, or
        None if the given key doesn't exist in the tree, or if is the maximum key,
        so the corresponding node has no successor.
        """
        node = self.find(key)
        return node and node.successor()
