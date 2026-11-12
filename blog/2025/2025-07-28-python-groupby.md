---
tags: python
date: "2025-07-28"
category: Python
author: Carlos Neto
title: "groupby + attrgetter: The Pythonic Way to Group Objects"
description: "How to group Python objects by several attributes with itertools.groupby and operator.attrgetter instead of a dictionary of lists, and why the input must be sorted by the same key first."
myst:
  html_meta:
    description: "How to group Python objects by several attributes with itertools.groupby and operator.attrgetter instead of a dictionary of lists, and why the input must be sorted by the same key first."
og:title: "groupby + attrgetter: The Pythonic Way to Group Objects"
og:description: "How to group Python objects by several attributes with itertools.groupby and operator.attrgetter instead of a dictionary of lists, and why the input must be sorted by the same key first."
---

*__Blog Post Publish Date:__ 2025/07/28*

---

# groupby + attrgetter: The Pythonic Way to Group Objects

This blog post shows how to group objects by several attributes. It uses two standard library tools, [itertools.groupby](https://docs.python.org/3/library/itertools.html#itertools.groupby) and [operator.attrgetter](https://docs.python.org/3/library/operator.html#operator.attrgetter), instead of building a dictionary of lists by hand. It also covers the one detail that trips most people up: `groupby` only groups items that are next to each other.

## The Example Data

To illustrate, here is a `Band` dataclass and a `bands` list. The goal is to group the bands by `category`, `genre`, and `country`, and print the names in each group.

```python
from dataclasses import dataclass

@dataclass
class Band:
    name: str
    category: str
    genre: str
    country: str

bands = [
    Band(name="The Beatles", category="Rock", genre="Rock", country="UK"),
    Band(name="Queen", category="Rock", genre="Rock", country="UK"),
    Band(name="The Rolling Stones", category="Rock", genre="Rock", country="UK"),
    Band(name="Led Zeppelin", category="Rock", genre="Rock", country="UK"),
    Band(name="The Who", category="Rock", genre="Rock", country="UK"),
    Band(name="Deep Purple", category="Rock", genre="Rock", country="UK"),
    Band(name="Nirvana", category="Rock", genre="Grunge", country="USA"),
    Band(name="Temple of the Dog", category="Rock", genre="Grunge", country="USA"),
    Band(name="Pearl Jam", category="Rock", genre="Grunge", country="USA"),
    Band(name="Soundgarden", category="Rock", genre="Grunge", country="USA"),
    Band(name="Alice in Chains", category="Rock", genre="Grunge", country="USA"),
    Band(name="Stone Temple Pilots", category="Rock", genre="Grunge", country="USA"),
    Band(name="Pink Floyd", category="Rock", genre="Progressive Rock", country="UK"),
    Band(name="Genesis", category="Rock", genre="Progressive Rock", country="UK"),
    Band(name="Yes", category="Rock", genre="Progressive Rock", country="UK"),
    Band(name="King Crimson", category="Rock", genre="Progressive Rock", country="UK"),
    Band(name="The Smiths", category="Rock", genre="Indie Rock", country="UK"),
    Band(name="Arctic Monkeys", category="Rock", genre="Indie Rock", country="UK"),
    Band(name="Pet Shop Boys", category="Pop", genre="Synth-pop", country="UK"),
    Band(name="Depeche Mode", category="Pop", genre="Synth-pop", country="UK"),
    Band(name="Erasure", category="Pop", genre="Synth-pop", country="UK"),
    Band(name="Korine", category="Pop", genre="Synth-pop", country="USA"),
    Band(name="Oasis", category="Rock", genre="Britpop", country="UK"),
    Band(name="Blur", category="Rock", genre="Britpop", country="UK"),
    Band(name="Pulp", category="Rock", genre="Britpop", country="UK"),
    Band(name="Echo & the Bunnymen", category="Rock", genre="Post-Punk", country="UK"),
    Band(name="Joy Division", category="Rock", genre="Post-Punk", country="UK"),
    Band(name="The Cure", category="Rock", genre="Post-Punk", country="UK"),
    Band(name="The Killers", category="Rock", genre="Alternative Rock", country="USA"),
    Band(name="R.E.M.", category="Rock", genre="Alternative Rock", country="USA"),
    Band(name="Radiohead", category="Rock", genre="Alternative Rock", country="UK"),
    Band(name="U2", category="Rock", genre="Rock", country="Ireland"),
]
```

## The Usual Approach: A Dictionary of Lists

The most common approach is a temporary dictionary whose key is a tuple of the grouping attributes and whose value is the list of objects that share them:

```python
bands_groupby_genre_country = {}

for band in bands:
    group_key = (band.category, band.genre, band.country)
    bands_groupby_genre_country.setdefault(group_key, []).append(band)

for (category, genre, country), band_group in bands_groupby_genre_country.items():
    print(f">>> {category=}, {genre=}, {country=}:")
    for band in band_group:
        print(f"- {band.name}")
```

It works, but the intent is buried in the bookkeeping: create the dictionary, build the key, append to the list, then loop again to read it.

## groupby With a Lambda

**`itertools.groupby`** is a standard library function that walks an iterable and yields one `(key, group)` pair for each run of consecutive items with the same key. It takes the iterable as its first argument and an optional `key` function. The `key` works exactly like the one in [sorted](https://docs.python.org/3/howto/sorting.html#key-functions): it is called for each item to compute the value to group by. In this example, a [lambda](https://docs.python.org/3/tutorial/controlflow.html#lambda-expressions) returns the `category`, `genre`, and `country` of each band:

```python
from itertools import groupby

attribute_group = lambda item: (item.category, item.genre, item.country)

for (category, genre, country), group in groupby(bands, key=attribute_group):
    print(f">>> {category=}, {genre=}, {country=}:")
    for band in group:
        print(f"  - {band.name}")
```

This already reads better: the loop says what it groups by and what it does with each group.

## groupby With attrgetter

**`operator.attrgetter`** returns a callable that reads the given attribute from its argument. With several attribute names, it returns a tuple of their values. For this purpose it does the same job as the lambda, but the code says what it does without the extra syntax:

```python
from operator import attrgetter
from itertools import groupby

attribute_group = attrgetter("category", "genre", "country",)

for (category, genre, country), group in groupby(bands, key=attribute_group):
    print(f">>> {category=}, {genre=}, {country=}:")
    for band in group:
        print(f"  - {band.name}")
```

The output is:

```
>>> category='Rock', genre='Rock', country='UK':
- The Beatles
- Queen
- The Rolling Stones
- Led Zeppelin
- The Who
- Deep Purple

>>> category='Rock', genre='Grunge', country='USA':
- Nirvana
- Temple of the Dog
- Pearl Jam
- Soundgarden
- Alice in Chains
- Stone Temple Pilots

>>> category='Rock', genre='Progressive Rock', country='UK':
- Pink Floyd
- Genesis
- Yes
- King Crimson

>>> category='Rock', genre='Indie Rock', country='UK':
- The Smiths
- Arctic Monkeys

>>> category='Pop', genre='Synth-pop', country='UK':
- Pet Shop Boys
- Depeche Mode
- Erasure

>>> category='Pop', genre='Synth-pop', country='USA':
- Korine

>>> category='Rock', genre='Britpop', country='UK':
- Oasis
- Blur
- Pulp

>>> category='Rock', genre='Post-Punk', country='UK':
- Echo & the Bunnymen
- Joy Division
- The Cure

>>> category='Rock', genre='Alternative Rock', country='USA':
- The Killers
- R.E.M.

>>> category='Rock', genre='Alternative Rock', country='UK':
- Radiohead

>>> category='Rock', genre='Rock', country='Ireland':
- U2
```

## Sort Before You Group

There is one catch. As the [itertools documentation](https://docs.python.org/3/library/itertools.html#itertools.groupby) says, `groupby` starts a new group every time the key changes. It only groups items that are next to each other. The `bands` list above is already ordered by group, which is why the output looks right. For example, if two UK rock bands were separated by a grunge band, they would end up in two different groups with the same key.

The dictionary approach doesn't have this problem, because it looks up the key for every item. For `groupby`, sort the data by the same key first:

```python
from operator import attrgetter
from itertools import groupby

attribute_group = attrgetter("category", "genre", "country")

for (category, genre, country), group in groupby(sorted(bands, key=attribute_group), key=attribute_group):
    print(f">>> {category=}, {genre=}, {country=}:")
    for band in group:
        print(f"  - {band.name}")
```

Reusing the same `attrgetter` for `sorted` and `groupby` keeps the two keys identical. Sorting changes the order of the groups, so the output is in alphabetical order of category, genre, and country.

For the full working example, see the [GitHub repository](https://github.com/c-neto/my-code-playground/blob/main/blog-code-examples/2025-07-28-groupby/python-groupby-example.py). You can also run it directly in your terminal:

```sh
curl -s https://raw.githubusercontent.com/c-neto/my-code-playground/refs/heads/main/blog-code-examples/2025-07-28-groupby/python-groupby-example.py | python -
```

If you like small standard library tricks like this, [Dynaconf](/blog/2024/2024-07-21-dynaconf.md) covers the other side of Python services I write often: configuration. And for instrumenting a Python application, see [OpenTelemetry: A Framework to Decoupling Your Observability](/blog/2026/2026-10-29-otel-foundation.md).

## Key Takeaways

- A dictionary of lists works for grouping, but the intent gets lost in the bookkeeping.
- `itertools.groupby(iterable, key=...)` yields one `(key, group)` pair per run of consecutive items with the same key.
- `operator.attrgetter("a", "b", "c")` builds the grouping key as a tuple, with no lambda.
- `groupby` only groups adjacent items, so sort with the same key first: `groupby(sorted(items, key=k), key=k)`.
- Both functions are in the standard library, so there is nothing to install.

## References

- [itertools.groupby (Python documentation)](https://docs.python.org/3/library/itertools.html#itertools.groupby)
- [operator.attrgetter (Python documentation)](https://docs.python.org/3/library/operator.html#operator.attrgetter)
- [Key functions (Python Sorting HOW TO)](https://docs.python.org/3/howto/sorting.html#key-functions)
- [Lambda expressions (Python tutorial)](https://docs.python.org/3/tutorial/controlflow.html#lambda-expressions)
- [Full example for this post (GitHub)](https://github.com/c-neto/my-code-playground/blob/main/blog-code-examples/2025-07-28-groupby/python-groupby-example.py)

---

> *I'm Carlos Neto, and this blog is where I share my experiences and open source contributions. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*

---

```{raw} html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "headline": "groupby + attrgetter: The Pythonic Way to Group Objects",
      "description": "How to group Python objects by several attributes with itertools.groupby and operator.attrgetter instead of a dictionary of lists, and why the input must be sorted by the same key first.",
      "datePublished": "2025-07-28",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2025/2025-07-28-python-groupby/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2025/2025-07-28-python-groupby/",
      "keywords": ["Python", "itertools.groupby", "operator.attrgetter", "grouping"],
      "author": {"@id": "https://carlosneto.dev/#person"}
    },
    {
      "@type": "Person",
      "@id": "https://carlosneto.dev/#person",
      "name": "Carlos Neto",
      "url": "https://carlosneto.dev/",
      "sameAs": ["https://www.linkedin.com/in/c-neto/", "https://github.com/c-neto"]
    },
    {
      "@type": "BreadcrumbList",
      "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://carlosneto.dev/"},
        {"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://carlosneto.dev/blog/"},
        {"@type": "ListItem", "position": 3, "name": "groupby + attrgetter: The Pythonic Way to Group Objects"}
      ]
    }
  ]
}
</script>
```
