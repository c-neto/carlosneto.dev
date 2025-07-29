---
tags: python
date: "2025-06-22"
category: code
---

*__Blog Post Publish Date:__ 2025/07/28*

---

# groupby + attrgetter = The Pythonic Way to Group Objects

This blog post explores an approach to group objects by mulitple attribute name powered by capabilities of the built-in modules [itertools.groupby](https://docs.python.org/3/library/itertools.html#itertools.groupby) and [operator.attrgetter](https://docs.python.org/3/library/operator.html#operator.attrgetter) module.

To illustrate this scenario, let's create a `Band` class, and a `bands` variable with a list of the instances. The objective is create groups by attributes `category`, `genre`, `country` and print the `name`.

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

The most common approach is to create a temporary dictionary where the key is a tuple of the attributes you want to group by, and the value is a list of objects that share those attributes:

```python
bands_groupby_genre_country = {}

for band in bands:
    group_key = (band.genre, band.country, band.category)
    bands_groupby_genre_country.setdefault(group_key, []).append(band)

for (category, genre, country), band_group in bands_groupby_genre_country.items():
    print(f">>> {category=}, {genre=}, {country=}:")
    for band in band_group:
        print(f"- {band.name}")
```

This approach works, but the code readability can cause confusion. Therefore, I present a more pythonic way to perform this operation using [groupby](https://docs.python.org/3/library/itertools.html#itertools.groupby) and [attrgetter](https://docs.python.org/3/library/operator.html#operator.attrgetter).

The [groupby](https://docs.python.org/3/library/itertools.groupby) function takes an iterable as its first positional argument and has an optional named argument `key`. The `key` works exactly the same way as in [sorted](https://docs.python.org/3/howto/sorting.html#key-functions), accepting a function that is called to determine the grouping. In the example below, the function is created using a [lambda](https://docs.python.org/2/tutorial/controlflow.html), where the groups are formed based on the `category`, `genre`, and `country` attributes.

```python
import group

group_tuple = lambda item: (item.category, item.genre, item.country)

for (category, genre, country), group in groupby(bands, key=group_tuple):
    print(f">>> {category=}, {genre=}, {country=}:")
    for band in group:
        print(f"  - {band.name}")
```

This approach offers better readability. However, by using the [attrgetter](https://docs.python.org/3/library/operator.html#operator.attrgetter) function, we can eliminate the [lambda](https://docs.python.org/2/tutorial/controlflow.html) and make the code more self-explanatory. The [attrgetter](https://docs.python.org/3/library/operator.html#operator.attrgetter) returns a callable object that fetches the specified attribute from its operand. If more than one attribute is requested, it returns a tuple of attributes. For practical purposes, this solution works the same way as the [lambda](https://docs.python.org/2/tutorial/controlflow.html), but the code is clearer and easier to understand.

```python
group_tuple = attrgetter("category", "genre", "country",)

for (category, genre, country), group in groupby(bands, key=group_tuple):
    print(f">>> {category=}, {genre=}, {country=}:")
    for band in group:
        print(f"  - {band.name}")
```

The script execution output will be:

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
- Thin Lizzy
```
