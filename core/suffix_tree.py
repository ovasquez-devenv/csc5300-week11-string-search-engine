"""Compressed suffix trie built with Ukkonen's algorithm.

Ukkonen's construction is O(n) and keeps the same compressed edge idea:
each edge is a slice of the text. A private sentinel character is appended
so every suffix ends at a leaf. Public queries talk about the original text
and do not return that sentinel.

This replaces the earlier builder that inserted one suffix at a time. That
builder was too heavy for a 1,000,000 character text.
"""

from __future__ import annotations


class Node:
    """One compressed edge, or the root when start is negative."""

    __slots__ = ("children", "suffix_link", "start", "end", "is_terminal")

    def __init__(self, start: int = -1, end: int | list[int] | None = None) -> None:
        self.children: dict[str, Node] = {}
        self.suffix_link: Node | None = None
        self.start = start
        self.end = end
        self.is_terminal = False

    def edge_end(self) -> int:
        end = self.end
        if isinstance(end, list):
            return end[0]
        return -1 if end is None else end


class SuffixTree:
    """Compressed trie over all suffixes of the text."""

    BUILD_ID = "ukkonen-v1"

    def __init__(self, text: str) -> None:
        self.text = text
        self.sentinel = _fresh_sentinel(text)
        self._work = text + self.sentinel
        self.root = Node()
        self.root.suffix_link = self.root
        self._leaf_end = [0]
        self._build()

    def _build(self) -> None:
        """Ukkonen. Leaf edges share _leaf_end so they grow each phase."""
        work = self._work
        n = len(work)
        root = self.root
        active_node = root
        active_edge = 0
        active_length = 0
        remainder = 0

        def edge_length(node: Node) -> int:
            return node.edge_end() - node.start

        for pos in range(n):
            self._leaf_end[0] = pos + 1
            remainder += 1
            last_internal: Node | None = None
            while remainder > 0:
                if active_length == 0:
                    active_edge = pos
                key = work[active_edge]
                if key not in active_node.children:
                    leaf = Node(start=pos, end=self._leaf_end)
                    leaf.is_terminal = True
                    active_node.children[key] = leaf
                    if last_internal is not None:
                        last_internal.suffix_link = active_node
                        last_internal = None
                else:
                    nxt = active_node.children[key]
                    length = edge_length(nxt)
                    if active_length >= length:
                        active_edge += length
                        active_length -= length
                        active_node = nxt
                        continue
                    if work[nxt.start + active_length] == work[pos]:
                        if last_internal is not None and active_node is not root:
                            last_internal.suffix_link = active_node
                            last_internal = None
                        active_length += 1
                        break
                    split_at = nxt.start + active_length
                    split = Node(start=nxt.start, end=split_at)
                    active_node.children[key] = split
                    leaf = Node(start=pos, end=self._leaf_end)
                    leaf.is_terminal = True
                    split.children[work[pos]] = leaf
                    nxt.start = split_at
                    split.children[work[nxt.start]] = nxt
                    if last_internal is not None:
                        last_internal.suffix_link = split
                    last_internal = split
                remainder -= 1
                if active_node is root and active_length > 0:
                    active_length -= 1
                    active_edge = pos - remainder + 1
                elif active_node is not root:
                    active_node = active_node.suffix_link or root
        self._freeze_leaf_ends()

    def _freeze_leaf_ends(self) -> None:
        final = self._leaf_end[0]
        stack = [self.root]
        while stack:
            node = stack.pop()
            if isinstance(node.end, list):
                node.end = final
            stack.extend(node.children.values())

    def _edge_label(self, node: Node) -> str:
        label = self._work[node.start : node.edge_end()]
        sentinel = self.sentinel
        if sentinel in label:
            label = label.replace(sentinel, "")
        return label

    def find_substring(self, pattern: str) -> bool:
        """True if pattern occurs anywhere in the text."""
        return self._walk(pattern) is not None

    def find_positions(self, pattern: str) -> list[int]:
        """Return every starting index of pattern in the original text."""
        n = len(self.text)
        m = len(pattern)
        if m == 0 or m > n:
            return []
        node = self.root
        depth = 0
        i = 0
        work = self._work
        while i < m:
            child = node.children.get(pattern[i])
            if child is None:
                return []
            end = child.edge_end()
            k = child.start
            while k < end and i < m:
                if work[k] != pattern[i]:
                    return []
                k += 1
                i += 1
            depth += end - child.start
            node = child
        positions: list[int] = []
        stack = [(node, depth)]
        while stack:
            current, current_depth = stack.pop()
            if current.is_terminal:
                start = len(work) - current_depth
                if 0 <= start < n:
                    positions.append(start)
            for nxt in current.children.values():
                stack.append((nxt, current_depth + (nxt.edge_end() - nxt.start)))
        positions.sort()
        return positions

    def find_prefix(self, prefix: str) -> list[str]:
        """Return suffixes of the text that start with prefix."""
        node = self._walk(prefix)
        if node is None:
            return []
        results: list[str] = []
        self._collect(node, prefix, results)
        return results

    def _walk(self, pattern: str) -> Node | None:
        node = self.root
        i = 0
        while i < len(pattern):
            child = node.children.get(pattern[i])
            if child is None:
                return None
            label = self._edge_label(child)
            k = 0
            while k < len(label) and i < len(pattern):
                if label[k] != pattern[i]:
                    return None
                k += 1
                i += 1
            if k < len(label) and i == len(pattern):
                return child
            if k == len(label) and i < len(pattern) and not child.children:
                return None
            node = child
        return node

    def _collect(self, node: Node, built: str, out: list[str]) -> None:
        if node.is_terminal or not node.children:
            if built and self.sentinel not in built:
                out.append(built)
        for child in node.children.values():
            self._collect(child, built + self._edge_label(child), out)

    def longest_repeated_substring(self) -> str:
        """Return one longest string that occurs at least twice."""
        best = ""

        def dfs(node: Node, path: str) -> None:
            nonlocal best
            if node is not self.root and node.children and len(path) > len(best):
                best = path
            for child in node.children.values():
                dfs(child, path + self._edge_label(child))

        dfs(self.root, "")
        return best

    def count_distinct_substrings(self) -> int:
        """Count distinct substrings of the original text.

        Edge lengths include one sentinel per leaf. Those sentinels are not
        part of the original text, so they are subtracted.
        """
        total = 0
        leaves = 0

        def dfs(node: Node) -> None:
            nonlocal total, leaves
            for child in node.children.values():
                total += child.edge_end() - child.start
                if not child.children:
                    leaves += 1
                dfs(child)

        dfs(self.root)
        return total - leaves


def _fresh_sentinel(text: str) -> str:
    code = 0xE000
    while True:
        sentinel = chr(code)
        if sentinel not in text:
            return sentinel
        code += 1
        if code > 0xF8FF:
            raise ValueError("text uses every private sentinel character")
