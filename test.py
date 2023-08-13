import wagner
import random
import hashlib
import timeit


def benchmark():
  n = 2 ** 64
  tree_height = 8
  List = wagner.ListFactory(n, tree_height=tree_height)

  l1 = List.generate(0)
  l2 = List.generate(1)
  l3 = List.generate(2)
  l4 = List.generate(3)
  l5 = List.generate(4)
  l6 = List.generate(5)
  l7 = List.generate(6)
  l8 = List.generate(7)

  print('binary merge h = 1:', timeit.timeit(lambda: l1 & l2, number=100))
  print('linear merge h = 1:', timeit.timeit(lambda: l1 ^ l2, number=100))

  l12 = l1 & l2
  l34 = l3 & l4
  l56 = l5 & l6
  l78 = l7 & l8

  print('binary merge h = 2:', timeit.timeit(lambda: l12 & l34, number=100))
  print('linear merge h = 2:', timeit.timeit(lambda: l12 ^ l34, number=100))

  l1234 = l12 & l34
  l5678 = l56 & l78

  print('binary merge h = 3:', timeit.timeit(lambda: l1234 & l5678, number=100))
  print('linear merge h = 3:', timeit.timeit(lambda: l1234 ^ l5678, number=100))


def hashfunc(r, n, index):
  r_bytes = r.to_bytes((int.bit_length(n) + 7) // 8, 'big')
  preimage = r_bytes + index.to_bytes(16, 'big')
  h = hashlib.sha256(preimage).digest()
  return int.from_bytes(h, 'big') % n


def shagen(n, index):
  r = random.randrange(0, n)
  return wagner.Lineage(hashfunc(r, n, index), r)


if __name__ == "__main__":
  benchmark()
  n = 2**80
  tree_height = None
  desired_sum = 0

  elements = wagner.solve(n, desired_sum, tree_height, generator=shagen)

  # print('solved with k = %d' % (len(elements)))
  # print(elements)

  assert sum((hashfunc(e, n, i) for i, e in enumerate(elements))) % n == 0, "desired sum"

  if tree_height is not None:
    assert len(elemenets) == 2**tree_height

  print('OK')
