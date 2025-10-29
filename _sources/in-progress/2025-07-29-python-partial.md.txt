---
tags: python
date: "2025-06-22"
category: code
---

*__Blog Post Publish Date:__ 2025/07/29*

---

# partial: simplify 

This Blog Post


```python
from functools import partial


def calc_concurrency(value: int, multiplier: int, symbol: str) -> str:
    return f"{symbol} {value * multiplier}"


dolar = partial(calc_concurrency, multiplier=5.58, symbol="US$")
euro = partial(calc_concurrency, multiplier=6.44, symbol="€")
yene = partial(calc_concurrency, multiplier=0.037, symbol="¥")

print(dolar(1))
print(euro(1))
print(yene(1))
```
