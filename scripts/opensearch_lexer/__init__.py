"""Pygments lexer for OpenSearch Dev Tools snippets (```opensearch blocks).

A snippet mixes three kinds of lines, as in the Dashboards Dev Tools console:

- ``# comment`` lines, highlighted like bash comments.
- Request lines (``GET /_cat/shards?v``), left unstyled.
- Request bodies, highlighted as JSON (NDJSON bodies work line by line).
"""
import re

from pygments.lexer import Lexer
from pygments.lexers.data import JsonLexer
from pygments.token import Comment, Text, Whitespace

_COMMENT_RE = re.compile(r"^[ \t]*#")
_REQUEST_RE = re.compile(r"^[ \t]*(GET|POST|PUT|DELETE|HEAD|PATCH)\b", re.IGNORECASE)


class OpenSearchLexer(Lexer):
    name = "OpenSearch"
    aliases = ["opensearch"]
    filenames = []

    def get_tokens_unprocessed(self, text):
        json_lexer = JsonLexer()
        body = []  # pending JSON lines
        body_start = 0
        pos = 0

        def flush():
            if body:
                chunk = "".join(body)
                for index, token, value in json_lexer.get_tokens_unprocessed(chunk):
                    yield body_start + index, token, value
                body.clear()

        for line in text.splitlines(keepends=True):
            content = line.rstrip("\r\n")
            newline = line[len(content):]
            if _COMMENT_RE.match(content) or _REQUEST_RE.match(content):
                yield from flush()
                token = Comment.Single if _COMMENT_RE.match(content) else Text
                yield pos, token, content
                if newline:
                    yield pos + len(content), Whitespace, newline
            else:
                if not body:
                    body_start = pos
                body.append(line)
            pos += len(line)
        yield from flush()

