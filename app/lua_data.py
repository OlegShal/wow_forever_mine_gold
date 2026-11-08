"""Парсер Lua-таблиц из файлов данных ForeverDB (Data/*.lua).

Только разбор литералов: таблицы, строки, числа, true/false/nil. Код Lua не исполняется.
"""
from __future__ import annotations

import re
from typing import Any

_ASSIGN = re.compile(r"^ns\.(\w+)\s*=\s*", re.M)
_NUMBER = re.compile(r"-?(?:0x[0-9a-fA-F]+|\d+\.?\d*(?:[eE][-+]?\d+)?|\.\d+(?:[eE][-+]?\d+)?)")
_NAME = re.compile(r"[A-Za-z_]\w*")
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'", "\n": "\n", "a": "\a", "b": "\b", "f": "\f", "v": "\v"}


class LuaParseError(ValueError):
    pass


def parse_ns_tables(text: str) -> dict[str, Any]:
    """Все присваивания вида `ns.name = <литерал>` на уровне файла."""
    out: dict[str, Any] = {}
    for m in _ASSIGN.finditer(text):
        p = _Parser(text, m.end())
        out[m.group(1)] = p.value()
    return out


class _Parser:
    def __init__(self, text: str, pos: int):
        self.s = text
        self.i = pos

    def _skip(self) -> None:
        s, n = self.s, len(self.s)
        while self.i < n:
            c = s[self.i]
            if c in " \t\r\n":
                self.i += 1
            elif s.startswith("--", self.i):
                if s.startswith("--[[", self.i):
                    end = s.find("]]", self.i + 4)
                    self.i = n if end < 0 else end + 2
                else:
                    end = s.find("\n", self.i)
                    self.i = n if end < 0 else end + 1
            else:
                break

    def _err(self, msg: str) -> LuaParseError:
        return LuaParseError(f"{msg} at {self.i}: {self.s[self.i:self.i + 40]!r}")

    def value(self) -> Any:
        self._skip()
        if self.i >= len(self.s):
            raise self._err("unexpected end")
        c = self.s[self.i]
        if c == "{":
            return self._table()
        if c in "\"'":
            return self._string(c)
        if self.s.startswith("true", self.i):
            self.i += 4
            return True
        if self.s.startswith("false", self.i):
            self.i += 5
            return False
        if self.s.startswith("nil", self.i):
            self.i += 3
            return None
        m = _NUMBER.match(self.s, self.i)
        if m:
            self.i = m.end()
            tok = m.group(0)
            if tok.lower().startswith(("0x", "-0x")):
                return int(tok, 16)
            return float(tok) if any(ch in tok for ch in ".eE") else int(tok)
        raise self._err("unexpected token")

    def _string(self, quote: str) -> str:
        s = self.s
        self.i += 1
        buf = []
        while True:
            if self.i >= len(s):
                raise self._err("unterminated string")
            c = s[self.i]
            if c == quote:
                self.i += 1
                return "".join(buf)
            if c == "\\":
                nxt = s[self.i + 1]
                if nxt.isdigit():
                    m = re.match(r"\d{1,3}", s[self.i + 1:])
                    buf.append(chr(int(m.group(0))))
                    self.i += 1 + len(m.group(0))
                    continue
                buf.append(_ESCAPES.get(nxt, nxt))
                self.i += 2
                continue
            buf.append(c)
            self.i += 1

    def _table(self) -> Any:
        self.i += 1  # {
        items: list[Any] = []
        keyed: dict[Any, Any] = {}
        while True:
            self._skip()
            if self.s[self.i] == "}":
                self.i += 1
                break
            if self.s[self.i] == "[":
                self.i += 1
                key = self.value()
                self._skip()
                self._expect("]")
                self._skip()
                self._expect("=")
                keyed[key] = self.value()
            else:
                m = _NAME.match(self.s, self.i)
                after = m and self.s[m.end():m.end() + 2].lstrip()
                j = m.end() if m else 0
                while m and j < len(self.s) and self.s[j] in " \t":
                    j += 1
                if m and j < len(self.s) and self.s[j] == "=" and self.s[j:j + 2] != "==" and m.group(0) not in ("true", "false", "nil"):
                    self.i = j + 1
                    keyed[m.group(0)] = self.value()
                else:
                    items.append(self.value())
            self._skip()
            if self.s[self.i] in ",;":
                self.i += 1
        if keyed and items:
            for n, v in enumerate(items, 1):
                keyed[n] = v
            return keyed
        return keyed if keyed else items

    def _expect(self, ch: str) -> None:
        if self.s[self.i] != ch:
            raise self._err(f"expected {ch!r}")
        self.i += 1
