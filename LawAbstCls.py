import os
import re
from collections import Counter
from EType import BASIC_ETYPE_SET, ETYPES_DICT, ETYPES

class LawAbstCls(object):
    def __init__(self, etypes=BASIC_ETYPE_SET):
        self.etypes = etypes
        self.root = None
        self._name = None
        self._num = None
        self._code = None

    def __str__(self):
        return "{name} ({num})".format(name=self.name, num=self.num)

    @property
    def name(self):
        if self._name is None:
            if self.root is not None:
                self._name = self.root.get_law_name()
        return "UNK" if self._name is None else self._name

    @property
    def num(self):
        if self._num is None:
            if self.root is not None:
                self._num = self.root.get_law_num()
        return "UNK" if self._num is None else self._num

    @property
    def code(self):
        if self._code is None:
            self._code = self._get_code()
        return self._code

    def _get_code(self):
        return "{0:02}/{1:06}/{2:04}".format(int(self.prefecture_code), int(self.municipality_code), int(self.file_code))

    def structure_check(self):
        for e in self.root.iter_descendants():
            e.structure_check()
        return True

    def get_plaintext(self):
        return "".join(self.root.iter_descendants().sentences)

    def iter_sentences(self, error_ok=False):
        for c in self.root.iter_descendants(error_ok=error_ok):
            for s in c.get_sentences():
                print(c)
                yield self.preprocess(s)

    def iter_leaves(self, error_ok=False):
        for ce in self.root.iter_descendants():
            if ce.is_leaf(error_ok):
                yield ce

    def is_reiki(self):
        return True if re.match("(?:例条|則規)", self.name[::-1]) else False

    def count_elems(self, error_ok=False):
        c = Counter()
        for ce in self.root.iter_descendants(error_ok=error_ok):
                c.update({ce.__class__.__name__: 1})
        return c

    def preprocess(self, s):
        return s

