"""Compressed trie suffix tree (Option A).

Built from the text by inserting every suffix into a compressed trie.
Supports substring queries, prefix matching, longest repeated substring,
and a count of distinct substrings.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Node:
    children: dict[str, "Node"] = field(default_factory=dict)
    start: int = -1
    end: int = -1
    is_terminal: bool = False


class SuffixTree:
    """Compressed trie over all suffixes of the text."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.root = Node()
        self._build()

    def _build(self) -> None:
        for i in range(len(self.text)):
            self._insert(i)

    def _insert(self, suffix_start: int) -> None:
        node = self.root
        i = suffix_start
        while i < len(self.text):
            ch = self.text[i]
            if ch not in node.children:
                child = Node(start=i, end=len(self.text))
                child.is_terminal = True
                node.children[ch] = child
                return
            child = node.children[ch]
            j = child.start
            while j < child.end and i < len(self.text) and self.text[j] == self.text[i]:
                j += 1
                i += 1
            if j == child.end:
                node = child
                continue
            # Split the edge.
            split = Node(start=child.start, end=j)
            child.start = j
            split.children[self.text[j]] = child
            node.children[ch] = split
            if i < len(self.text):
                leaf = Node(start=i, end=len(self.text))
                leaf.is_terminal = True
                split.children[self.text[i]] = leaf
            else:
                split.is_terminal = True
            return
        node.is_terminal = True

    def _edge_label(self, node: Node) -> str:
        return self.text[node.start : node.end]

    def find_substring(self, pattern: str) -> bool:
        """True if pattern occurs anywhere in the text."""
        return self._walk(pattern) is not None

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
            ch = pattern[i]
            if ch not in node.children:
                return None
            child = node.children[ch]
            label = self._edge_label(child)
            k = 0
            while k < len(label) and i < len(pattern):
                if label[k] != pattern[i]:
                    return None
                k += 1
                i += 1
            if k < len(label) and i == len(pattern):
                return child
            node = child
        return node

    def _collect(self, node: Node, built: str, out: list[str]) -> None:
        if node.is_terminal or not node.children:
            out.append(built)
        for child in node.children.values():
            self._collect(child, built + self._edge_label(child), out)

    def longest_repeated_substring(self) -> str:
        """Return one longest string that occurs at least twice."""
        best = ""

        def dfs(node: Node, depth: int, path: str) -> None:
            nonlocal best
            branches = len(node.children)
            terminal_extra = 1 if node.is_terminal else 0
            if branches + terminal_extra >= 2 and len(path) > len(best):
                best = path
            for child in node.children.values():
                label = self._edge_label(child)
                dfs(child, depth + len(label), path + label)

        dfs(self.root, 0, "")
        return best

    def count_distinct_substrings(self) -> int:
        """Count distinct substrings as the sum of compressed edge lengths."""
        total = 0

        def dfs(node: Node) -> None:
            nonlocal total
            for child in node.children.values():
                total += child.end - child.start
                dfs(child)

        dfs(self.root)
        return total
