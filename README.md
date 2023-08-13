# wagner

Python implementation of [Wagner's Algorithm for the Generalized Birthday Problem](https://link.springer.com/content/pdf/10.1007/3-540-45708-9_19.pdf).

This algorithm is used to solve what is known as the generalized birthday problem. Given a modulus $n$, and $k$ lists of random numbers $\\{L_1, L_2, ..., L_k\\}$, how can we find $k$ elements $\\{x_1, x_2, ..., x_k\\} : x_i \in L_i$ from those lists, such that they all sum to some constant $c$ mod $n$?

[Check out my full-length article on the subject](https://conduition.io/cryptography/wagner) for more detailed info. This repository is meant as a demonstration for practically minded and inquisitive readers.

## Usage

The primary export of this library is the `solve` method.

```python
>>> import wagner
>>> wagner.solve(2**16)
[50320, 16960, 11687, 52082, 17220, 47751, 11228, 54896]
>>> sum(_) % (2**16)
0
```

This method solves the generalized birthday problem for a given modulus $n$. The higher $n$ is, the more difficult it is to find a solution and the longer the algorithm will take.

At no cost, the caller can also choose a desired sum other than zero.

```python
n = 2 ** 16
sum(wagner.solve(n, 885)) % n # -> 885
```

To change the number of elements returned by `solve`, specify the height $H$ of the tree used to solve the problem. The number of elements in the solution will be $2^H$.

```python
len(wagner.solve(n, tree_height=2)) # -> 4
len(wagner.solve(n, tree_height=3)) # -> 8
len(wagner.solve(n, tree_height=4)) # -> 16
len(wagner.solve(n, tree_height=5)) # -> 32
```

To specify how the random elements are generated, provide a `generator` callback. By default, `wagner` uses `random.randrange(n)` to generate random values. A common use case for Wagner's Algorithm is to find inputs whose hashes sum to some desired number. To ensure `solve` returns the preimages and not the hash outputs, return `Lineage` instances from your `generator` callback. This class holds is basically an integer with pointers to the element(s) which created it.

```python
import random
import hashlib
import wagner


def hashfunc(r, n, index):
  r_bytes = r.to_bytes((int.bit_length(n) + 7) // 8, 'big')
  preimage = r_bytes + index.to_bytes(16, 'big')
  h = hashlib.sha1(preimage).digest()
  return int.from_bytes(h, 'big') % n


def generator(n, index):
  r = random.randrange(0, n)
  return wagner.Lineage(hashfunc(r, n, index), r)


if __name__ == "__main__":
  n = 2 ** 128
  preimages = wagner.solve(n, generator=generator)
  print(sum(hashfunc(r, n, index) for index, r in enumerate(preimages)) % n) # -> 0
```
