from math import log2, inf
import random
from bisect import bisect_left


class Lineage(int):
  """
  Lineage represents an integer and pointers to ancestor objects which created it.
  """
  def __new__(cls, x, *ancestors):
    el = int.__new__(cls, x)
    el._ancestors = ancestors
    return el

  def ancestors(self):
    """
    Returns any ancestor values which were used to create the instance.
    Operates recursively, walking up to the oldest ancestor values.
    """
    if len(self._ancestors) == 0:
      return [self]
    ancestors = []
    for ancestor in self._ancestors:
      if type(ancestor) == Lineage:
        ancestors.extend(ancestor.ancestors())
      else:
        ancestors.append(ancestor)
    return ancestors


def find_best_tree_height(n):
  """
  Finds the optimal tree height for a given modulus of n to
  minimize the computations required to find a solution.
  """
  log_n = int(log2(n))
  min_computations = inf
  best_tree_height = 1
  for tree_height in range(2, log_n):
    k = 2 ** tree_height
    lamda = n ** (1 / (1 + tree_height))
    computations = round((k - 2) * (2 * lamda * (log2(lamda) + 1)))

    if computations < min_computations:
      min_computations = computations
      best_tree_height = tree_height
    else:
      return best_tree_height
  return log_n


def default_generator(n, i):
  """
  Generates a random number using random.randrange(n). Used as the default
  List element generating callback if one is not given.
  """
  return random.randrange(n)


def ListFactory(n, desired_sum=0, tree_height=None, generator=default_generator):
  """
  Creates a List class used to solve a given class of birthday problem, over the
  given modulus n. Most use-cases will want to use the top-level solve method
  instead.
  """
  if tree_height is None:
    tree_height = find_best_tree_height(n)

  list_length = round(n ** (1 / (1 + tree_height)))
  k = 2 ** tree_height
  half_n = n >>  1

  if desired_sum >= n:
    raise RuntimeError("desired sum is greater than modulus")


  def filter_range(h):
    if h == tree_height:
      return (n, 0)
    divisor = 2 * (list_length ** h)
    base = round(n / divisor)
    a = n - base
    b = base - 1
    return (a, b)

  # cache the filter ranges in advance so we don't
  # recompute them for every merge operation.
  filter_ranges = [None] + [filter_range(h) for h in range(1, tree_height + 1)]


  class List:
    """
    List represents a list of random elements, either the result of previous list merging
    operations, or a freshly generated leaf list itself.

    Most use cases should use the top-level solve method instead.
    """

    def __init__(self, items, height):
      self.items = items
      self.height = height

    def generate(index):
      """
      Generates a new list at height zero (a leaf list) with the given
      index. If the index indicates the List will be the last in the whole
      set of k lists (i.e. index == k - 1), then the desired sum will be
      subtracted from each element after it is generated.
      """
      items = [generator(n, index) for _ in range(list_length)]
      # The last list must be modified to produce a set with our desired sum.
      # Include a pointer back to the original random number.
      if index+1 == k:
        for (i, x) in enumerate(items):
          items[i] = Lineage((x - desired_sum) % n, x)

      return List(items, 0)

    def __iter__(self):
      return iter(self.items)
    def __len__(self):
      return len(self.items)
    def __getitem__(self, i):
      return self.items[i]

    # inefficient example merging operator.
    # merges lists by iterating through every sum.
    def __xor__(L1, L2):
      a, b = filter_ranges[L1.height + 1]
      sums = []
      for e1 in L1:
        for e2 in L2:
          z = (e1 + e2) % n
          if z >= a or z <= b:
            sums.append(Lineage(z, e1, e2))
      return List(sums, L1.height + 1)


    # fast merge using sorting and binary-search.
    def __and__(L1, L2):
      a, b = filter_ranges[L1.height + 1]
      sums = []

      # sort L2 so we can perform binary searches on it.
      sorted_other_items = sorted(L2)

      l2_min = sorted_other_items[0]
      l2_max = sorted_other_items[-1]

      for e1 in L1:
        # find the range in L2 within which e1 + e2 could fall into [a, b].
        # e2 = a - e1 will be the minimum number needed so that e1 + e2 = a.
        #
        # bisect_left will return the index of (a - e1) if it exists in sorted_other_items.
        # Otherwise it will return the location in L2 where (a - e1) would exist.
        #
        # Explore to the right through this range, wrapping around the end of the list
        # until we run out of useful elements.
        min_e2 = (a - e1) % n
        min_index = bisect_left(sorted_other_items, min_e2)
        index = min_index

        # Give up once we cycle through the whole list.
        while index < min_index + len(sorted_other_items):
          e2 = sorted_other_items[index % len(sorted_other_items)]
          z = (e1 + e2) % n
          if z >= a or z <= b:
            sums.append(Lineage(z, e1, e2))
          else:
            break # no more useful elements to be found.
          index += 1

      return List(sums, L1.height + 1)

    def at_height(height, index=None):
      """
      Recursively build a List at a given height in the tree. If height > 1,
      this function builds parent Lists and merges them together recursively
      until finally merging a List at the desired height, which is then
      returned to the caller.
      """
      if height < 1:
        raise RuntimeError("invalid height %d" % height)

      # Each leaf list should be passed an index from 0 to (k-1) to help
      # parameterize list generation. Since leaf lists are generated lazily,
      # we need to compute which index should be given to each parent list.
      #
      # - Start at the root node with the maximum index k - 1.
      # - The right-side parent's index should be the same as the child's index.
      # - The left parent's index should be: child_index - (2 ** parent_height)
      #
      # This propagates the correct list indices up the tree to the leaf lists.
      #
      # 0     1   2     3   4     5   6     7     h = 0
      # │     │   │     │   │     │   │     │
      # └─ 1 ─┘   └─ 3 ─┘   └─ 5 ─┘   └─ 7 ─┘     h = 1
      #    │         │         │         │
      #    └─── 3 ───┘         └─── 7 ───┘        h = 2
      #         │                   │
      #         └──────── 7 ────────┘             h = 3
      if index is None:
        index = (1 << height) - 1
      right_index = index
      left_index = index - (1 << (height - 1))

      merged = List([], height)
      while len(merged) == 0:
        if height == 1:
          left = List.generate(left_index)
          right = List.generate(right_index)
        else:
          left = List.at_height(height - 1, left_index)
          right = List.at_height(height - 1, right_index)

        # Uncomment to use the binary-search driven merge.
        merged = left & right

        # Uncomment to use the naive sequential merge.
        # merged = left ^ right

      return merged

  return List

def solve(n, desired_sum=0, tree_height=None, generator=default_generator):
  """
  Compute a solution to the generalized birthday problem modulo n. Outputs
  a list of integers which sum to the given desired_sum modulo n.

  By default solve will automatically compute the optimal number of lists needed for
  computing a solution quickly. If the caller would like to specify a certain number
  of output values k, simply supply the tree_height parameter such that k = 2 ** tree_height,
  (k must be a power of two).

  Leaf elements will be generated randomly by default. Callers may pass a generator
  function g(n, i). This function takes the modulus n and the list index i (lists are
  indexed from zero) and should output a random integer or Lineage instance.

  If the caller wishes to generate pseudo-random list elements by hashing randomized
  input data, they can make solve return the hash function's input data by returning
  Lineage instances in the generator function. See the readme for details.
  """
  if tree_height is None:
    tree_height = find_best_tree_height(n)

  List = ListFactory(n, desired_sum, tree_height, generator)
  root = List.at_height(tree_height)
  return root[0].ancestors()
