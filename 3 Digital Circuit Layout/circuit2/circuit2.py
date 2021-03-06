#!/usr/bin/env python

import json   # Used when TRACE=jsonp
import os     # Used to get the TRACE environment variable
import re     # Used when TRACE=jsonp
import sys    # Used to smooth over the range / xrange issue.
import avl    # Used in RangeIndex

# Python 3 doesn't have xrange, and range behaves like xrange.
if sys.version_info >= (3,):
    xrange = range

# Circuit verification library.


class Wire(object):
    """A wire in an on-chip circuit.

    Wires are immutable, and are either horizontal or vertical.
    """

    def __init__(self, name, x1, y1, x2, y2):
        """Creates a wire.

        Raises an ValueError if the coordinates don't make up a horizontal wire
        or a vertical wire.

        Args:
          name: the wire's user-visible name
          x1: the X coordinate of the wire's first endpoint
          y1: the Y coordinate of the wire's first endpoint
          x2: the X coordinate of the wire's last endpoint
          y2: the Y coordinate of the wire's last endpoint
        """
        # Normalize the coordinates.
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1

        self.name = name
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.object_id = Wire.next_object_id()

        if not (self.is_horizontal() or self.is_vertical()):
            raise ValueError(str(self) + ' is neither horizontal nor vertical')

    def is_horizontal(self):
        """True if the wire's endpoints have the same Y coordinates."""
        return self.y1 == self.y2

    def is_vertical(self):
        """True if the wire's endpoints have the same X coordinates."""
        return self.x1 == self.x2

    def intersects(self, other_wire):
        """True if this wire intersects another wire."""
        # NOTE: we assume that wires can only cross, but not overlap.
        if self.is_horizontal() == other_wire.is_horizontal():
            return False

        if self.is_horizontal():
            h = self
            v = other_wire
        else:
            h = other_wire
            v = self
        return v.y1 <= h.y1 and h.y1 <= v.y2 and h.x1 <= v.x1 and v.x1 <= h.x2

    def __repr__(self):
        # :nodoc: nicer formatting to help with debugging
        return('<wire ' + self.name + ' (' + str(self.x1) + ',' + str(self.y1) +
               ')-(' + str(self.x2) + ',' + str(self.y2) + ')>')

    def as_json(self):
        """Dict that obeys the JSON format restrictions, representing the wire."""
        return {'id': self.name, 'x': [self.x1, self.x2], 'y': [self.y1, self.y2]}

    # Next number handed out by Wire.next_object_id()
    _next_id = 0

    @staticmethod
    def next_object_id():
        """Returns a unique numerical ID to be used as a Wire's object_id."""
        id = Wire._next_id
        Wire._next_id += 1
        return id


class WireLayer(object):
    """The layout of one layer of wires in a chip."""

    def __init__(self):
        """Creates a layer layout with no wires."""
        self.wires = {}

    def wires(self):
        """The wires in the layout."""
        self.wires.values()

    def add_wire(self, name, x1, y1, x2, y2):
        """Adds a wire to a layer layout.

        Args:
          name: the wire's unique name
          x1: the X coordinate of the wire's first endpoint
          y1: the Y coordinate of the wire's first endpoint
          x2: the X coordinate of the wire's last endpoint
          y2: the Y coordinate of the wire's last endpoint

        Raises an exception if the wire isn't perfectly horizontal (y1 = y2) or
        perfectly vertical (x1 = x2)."""
        if name in self.wires:
            raise ValueError('Wire name ' + name + ' not unique')
        self.wires[name] = Wire(name, x1, y1, x2, y2)

    def as_json(self):
        """Dict that obeys the JSON format restrictions, representing the layout."""
        return {'wires': [wire.as_json() for wire in self.wires.values()]}

    @staticmethod
    def from_file(file):
        """Builds a wire layer layout by reading a textual description from a file.

        Args:
          file: a File object supplying the input

        Returns a new Simulation instance."""

        layer = WireLayer()

        while True:
            command = file.readline().split()
            if command[0] == 'wire':
                coordinates = [float(token) for token in command[2:6]]
                layer.add_wire(command[1], *coordinates)
            elif command[0] == 'done':
                break

        return layer


class RangeNode(avl.AVLNode):
    """A node in a range tree."""

    def __init__(self, key):
        """Creates a node that will be inserted in a range index tree.

        See __init__ in BSTNode."""
        avl.AVLNode.__init__(self, key)
        self.tree_size = 1

    def update_subtree_info(self):
        """Updates pre-computed fields such as the node's subtree height."""
        avl.AVLNode.update_subtree_info(self)
        self.tree_size = self._uncached_tree_size()

    def _uncached_tree_size(self):
        """Re-computes the node's subtree size based on the children's heights."""
        return 1 + (((self.left and self.left.tree_size) or 0) +
                    ((self.right and self.right.tree_size) or 0))

    def rank(self, key):
        """Number of keys <= the given key in the subtree rooted at this node."""
        if key < self.key:
            if self.left is not None:
                return self.left.rank(key)
            else:
                return 0
        if self.left:
            lrank = 1 + self.left.tree_size
        else:
            lrank = 1
        if key > self.key and self.right is not None:
            return lrank + self.right.rank(key)
        return lrank

    def list(self, first_key, last_key, result):
        """Lists nodes with keys between first_key and last_key in this node's subtree.

        Extends result with a list of RangeNode instances for the nodes in the
        subtree rooted at this node, such that each node's key is between first_key
        and last_key."""
        if first_key <= self.key <= last_key:
            result.append(self.key)
        if self.left is not None and first_key <= self.key:
            self.left.list(first_key, last_key, result)
        if self.right is not None and self.key <= last_key:
            self.right.list(first_key, last_key, result)

    def lca(self, first_key, last_key):
        """Lowest-common ancestor node of nodes with first_key and last_key.

        If first_key and/or last_key are not in the tree, this returns the LCA of the
        nodes that would be created by inserting the keys in the tree.

        Returns a RangeNode instance, or None if first_key and last_key are not in the
        node's subtree, and there is no key in the tree such that
        first_key < key < last_key.
        """
        if first_key <= self.key <= last_key:
            return self
        if first_key < self.key:
            return self.left and self.left.lca(first_key, last_key)
        else:
            return self.right and self.right.lca(first_key, last_key)


class RangeIndex(avl.AVL):
    """BST with support for range queries."""

    def __init__(self, node_class=RangeNode):
        """Creates an empty AVL tree.

        Args:
          node_class (optional): the class of nodes in the tree, defaults to AVLNode
        """
        avl.AVL.__init__(self, node_class)

    def add(self, key):
        """Inserts a key in the range index."""
        if key is None:
            raise ValueError('Cannot insert None in the index')
        self.insert(key)

    def remove(self, key):
        """Removes a key from the range index."""
        self.delete(key)

    def lca(self, first_key, last_key):
        """Lowest-common ancestor node of nodes with first_key and last_key.

        If first_key and/or last_key are not in the tree, this returns the LCA of the
        nodes that would be created by inserting the keys in the tree.

        Returns a RangeNode instance, or None if first_key and last_key are not in the
        tree, and there is no key in the tree such that first_key < key < last_key.
        """
        return self.root and self.root.lca(first_key, last_key)

    def list(self, first_key, last_key):
        """List of values for the keys that fall within [first_key, last_key]."""
        result = []
        lca = self.lca(first_key, last_key)
        if lca is not None:
            lca.list(first_key, last_key, result)
        return result

    def rank(self, key):
        """Number of keys <= the given key in the tree."""
        if self.root is not None:
            return self.root.rank(key)
        return 0

    def count(self, first_key, last_key):
        """Number of keys that fall within [first_key, last_key]."""
        return self.rank(last_key) - self.rank(first_key)


class TracedRangeIndex(RangeIndex):
    """Augments RangeIndex to build a trace for the visualizer."""

    def __init__(self, trace):
        """Sets the object receiving tracing info."""
        RangeIndex.__init__(self)
        self.trace = trace

    def add(self, key):
        self.trace.append({'type': 'add', 'id': key.wire.name})
        RangeIndex.add(self, key)

    def remove(self, key):
        self.trace.append({'type': 'delete', 'id': key.wire.name})
        RangeIndex.remove(self, key)

    def list(self, first_key, last_key):
        result = RangeIndex.list(self, first_key, last_key)
        self.trace.append({'type': 'list', 'from': first_key.key,
                           'to': last_key.key,
                           'ids': [key.wire.name for key in result]})
        return result

    def count(self, first_key, last_key):
        result = RangeIndex.count(self, first_key, last_key)
        self.trace.append({'type': 'list', 'from': first_key.key,
                           'to': last_key.key, 'count': result})
        return result


class ResultSet(object):
    """Records the result of the circuit verifier (pairs of crossing wires)."""

    def __init__(self):
        """Creates an empty result set."""
        self.crossings = []

    def add_crossing(self, wire1, wire2):
        """Records the fact that two wires are crossing."""
        self.crossings.append(sorted([wire1.name, wire2.name]))

    def write_to_file(self, file):
        """Write the result to a file."""
        for crossing in self.crossings:
            file.write(' '.join(crossing))
            file.write('\n')


class TracedResultSet(ResultSet):
    """Augments ResultSet to build a trace for the visualizer."""

    def __init__(self, trace):
        """Sets the object receiving tracing info."""
        ResultSet.__init__(self)
        self.trace = trace

    def add_crossing(self, wire1, wire2):
        self.trace.append({'type': 'crossing', 'id1': wire1.name,
                           'id2': wire2.name})
        ResultSet.add_crossing(self, wire1, wire2)


class KeyWirePair(object):
    """Wraps a wire and the key representing it in the range index.

    Once created, a key-wire pair is immutable."""

    def __init__(self, key, wire):
        """Creates a new key for insertion in the range index."""
        self.key = key
        if wire is None:
            raise ValueError('Use KeyWirePairL or KeyWirePairH for queries')
        self.wire = wire
        self.wire_id = wire.object_id

    def __lt__(self, other):
        # :nodoc: Delegate comparison to keys.
        return (self.key < other.key or
                (self.key == other.key and self.wire_id < other.wire_id))

    def __le__(self, other):
        # :nodoc: Delegate comparison to keys.
        return (self.key < other.key or
                (self.key == other.key and self.wire_id <= other.wire_id))

    def __gt__(self, other):
        # :nodoc: Delegate comparison to keys.
        return (self.key > other.key or
                (self.key == other.key and self.wire_id > other.wire_id))

    def __ge__(self, other):
        # :nodoc: Delegate comparison to keys.
        return (self.key > other.key or
                (self.key == other.key and self.wire_id >= other.wire_id))

    def __eq__(self, other):
        # :nodoc: Delegate comparison to keys.
        return self.key == other.key and self.wire_id == other.wire_id

    def __ne__(self, other):
        # :nodoc: Delegate comparison to keys.
        return self.key == other.key and self.wire_id == other.wire_id

    def __hash__(self):
        # :nodoc: Delegate comparison to keys.
        return hash([self.key, self.wire_id])

    def __repr__(self):
        # :nodoc: nicer formatting to help with debugging
        return '<key: ' + str(self.key) + ' wire: ' + str(self.wire) + '>'


class KeyWirePairL(KeyWirePair):
    """A KeyWirePair that is used as the low end of a range query.

    This KeyWirePair is smaller than all other KeyWirePairs with the same key."""

    def __init__(self, key):
        self.key = key
        self.wire = None
        self.wire_id = -1000000000


class KeyWirePairH(KeyWirePair):
    """A KeyWirePair that is used as the high end of a range query.

    This KeyWirePair is larger than all other KeyWirePairs with the same key."""

    def __init__(self, key):
        self.key = key
        self.wire = None
        # HACK(pwnall): assuming 1 billion objects won't fit into RAM.
        self.wire_id = 1000000000


class CrossVerifier(object):
    """Checks whether a wire network has any crossing wires."""

    def __init__(self, layer):
        """Verifier for a layer of wires.

        Once created, the verifier can list the crossings between wires (the
        wire_crossings method) or count the crossings (count_crossings)."""

        self.events = []
        self._events_from_layer(layer)
        self.events.sort()

        self.index = RangeIndex()
        self.result_set = ResultSet()
        self.performed = False

    def count_crossings(self):
        """Returns the number of pairs of wires that cross each other."""
        if self.performed:
            raise
        self.performed = True
        return self._compute_crossings(True)

    def wire_crossings(self):
        """An array of pairs of wires that cross each other."""
        if self.performed:
            raise
        self.performed = True
        return self._compute_crossings(False)

    def _events_from_layer(self, layer):
        """Populates the sweep line events from the wire layer."""
        for wire in layer.wires.values():
            if wire.is_horizontal():
                self.events.append(
                    [wire.x1, 0, wire.object_id, 'add', wire])
                self.events.append(
                    [wire.x2, 2, wire.object_id, 'remove', wire])
            else:
                self.events.append(
                    [wire.x1, 1, wire.object_id, 'query', wire])

    def _compute_crossings(self, count_only):
        """Implements count_crossings and wire_crossings."""
        if count_only:
            result = 0
        else:
            result = self.result_set

        for event in self.events:
            event_x, event_type, wire = event[0], event[3], event[4]
            self.trace_sweep_line(event_x)

            if event_type == 'add':
                self.index.add(KeyWirePair(wire.y1, wire))
            elif event_type == 'remove':
                self.index.remove(KeyWirePair(wire.y1, wire))
            elif event_type == 'query':
                if count_only:
                    result += self.index.count(KeyWirePairL(wire.y1),
                                               KeyWirePairH(wire.y2))
                else:
                    for cross_wire in self.index.list(KeyWirePairL(wire.y1),
                                                      KeyWirePairH(wire.y2)):
                        result.add_crossing(wire, cross_wire.wire)

        return result

    def trace_sweep_line(self, x):
        """When tracing is enabled, adds info about where the sweep line is.

        Args:
          x: the coordinate of the vertical sweep line
        """
        # NOTE: this is overridden in TracedCrossVerifier
        pass


class TracedCrossVerifier(CrossVerifier):
    """Augments CrossVerifier to build a trace for the visualizer."""

    def __init__(self, layer):
        CrossVerifier.__init__(self, layer)
        self.trace = []
        self.index = TracedRangeIndex(self.trace)
        self.result_set = TracedResultSet(self.trace)

    def trace_sweep_line(self, x):
        self.trace.append({'type': 'sweep', 'x': x})

    def trace_as_json(self):
        """List that obeys the JSON format restrictions with the verifier trace."""
        return self.trace


# Command-line controller.
if __name__ == '__main__':
    import sys
    layer = WireLayer.from_file(sys.stdin)
    verifier = CrossVerifier(layer)

    if os.environ.get('TRACE') == 'jsonp':
        verifier = TracedCrossVerifier(layer)
        result = verifier.wire_crossings()
        json_obj = {'layer': layer.as_json(
        ), 'trace': verifier.trace_as_json()}
        sys.stdout.write('onJsonp(')
        json.dump(json_obj, sys.stdout)
        sys.stdout.write(');\n')
    elif os.environ.get('TRACE') == 'list':
        verifier.wire_crossings().write_to_file(sys.stdout)
    else:
        sys.stdout.write(str(verifier.count_crossings()) + "\n")
