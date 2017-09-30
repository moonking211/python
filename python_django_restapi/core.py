# encoding: utf-8

from __future__ import unicode_literals


class LinkedList(object):
    """Linked list implementation."""

    class LinkedListItem(object):
        def __init__(self, value):
            self.value, self.prev, self.next = value, None, None

    def __init__(self):
        self._head = None
        self._tail = None

    def add(self, value):
        """Adds a given item to the end of the list.

        :param value:
        :return:
        """
        new_node = LinkedList.LinkedListItem(value)
        if not self._head:
            self._head = self._tail = new_node
        else:
            self._tail.next, new_node.prev, self._tail = new_node, self._tail, new_node

    @property
    def head(self):
        """Returns first list item."""
        return self._head

    @property
    def tail(self):
        """Returns last list item."""
        return self._tail

    def removeFirst(self):
        """Removes and returns the first item from the list."""
        ret = None
        if self._tail == self._head:
            ret, self._tail, self._head = self._head, None, None
        elif self._head:
            ret, self._head = self._head, self._head.next
        if self._head:
            self._head.prev = None
        return ret.value if ret else ret

    def removeLast(self):
        """Removes and returns the last item from the list."""
        if self._tail == self._head:
            ret, self._tail, self._head = self._tail, None, None
        else:
            ret, self._head = self._head, self._head.next if self._head else None
        return ret.value if ret else ret


def own_filter_kwargs(registry, own_key__field):
    """Returns kwargs for filtering entities that are owned by the registry user."""
    filter_kwargs = {}
    for key, field in own_key__field:
        ids = registry.get(key)
        if ids:
            if len(ids) > 1:
                filter_kwargs['{}__in'.format(field)] = ids
            else:
                filter_kwargs[field] = ids[0]
    return filter_kwargs


def safe_to_int(v):
    """Safely converts given value to int, if value cannot be converted to int returns None."""
    try:
        return int(v)
    except (TypeError, ValueError):
        pass
