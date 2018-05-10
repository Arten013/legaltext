from LawError import *
from LawElementBase import *
from EType import *
import re
from abc import abstractmethod
from LawElementNumber import LawElementNumber
from TextIO import kansuji2arabic as kan_ara

class RootBase(LawElementBase):
	def __init__(self, lawdata, parent=None):
		assert parent is None
		self.parent = None
		self.lawdata = lawdata
		self.etypes = self.lawdata.etypes
		self.child_etype = None
		self._num = None
		self._child = None

	def __str__(self):
		return self.lawdata.name

	@property
	def id(self):
		try:
			return int(self.lawdata.oid) * (-1)
		except:
			raise
			return -1

	@abstractmethod
	def get_law_name(self):
		pass

	@abstractmethod
	def get_law_num(self):
		pass

	def get_number(self):
		return LawElementNumber(self.etype, "0")

	def parent_check(self):
		return True

	def _check_child(self, e, error_ok):
		if not e.__class__.__name__ in ["MainProvision", "SupplProvision"]:
			return False
		if not e.__class__.__name__ in self.etypes:
			return False
		if error_ok:
			return True
		return self.structure_check()

class ProvBase(LawElementBase):
	def parent_check(self):
		if not issubclass(self.parent.__class__, RootBase):
			raise HieralchyError(self.lawdata, "invalid hieralchy "+self.parent.__class__.__name__ + " -> " + self.__class__.__name__)

	def __str__(self):
		return str(self.parent)+"("+ETYPES_DICT[self.__class__.__name__]+")"

	def get_number(self):
		return LawElementNumber(self.etype, "0")

class SuperordinateElementBase(LawElementBase):
	pass

class BasicElementBase(LawElementBase):
	pass

class ItemBase(BasicElementBase):
    pass

class TextBase(LawElementBase):
	def __init__(self, lawdata, parent):
		self.parent = parent
		self.lawdata = lawdata
		self.etypes = parent.etypes
		self._num = None
		self.id = None

	def inheritance(self):
		self.texts = self.extract_text()

	def __str__(self):
		return str(self.parent)+str(self.get_number())
	def is_leaf(self, error_ok):
		return True

	def number_check(self):
		return True

	def brothers_check(self):
		return True

	def iter_children(self, error_ok=False):
		return []

	def iter_descendants(self, error_ok=False):
		return []

	def get_sentences(self):
		yield from self.texts

	def _iter_possible_children(self):
		yield from []

	@abstractmethod
	def extract_text(self):
		pass

class CaptionBase(TextBase):
	def get_number(self):
		return LawElementNumber(self.etype, "0")

	def __str__(self):
		return str(self.parent)+ETYPES_DICT[self.__class__.__name__]

class SentenceBase(TextBase):
	pass

class ItemSentenceBase(TextBase):
	def parent_check(self):
		if not issubclass(self.parent.__class__, ItemBase):
			raise HieralchyError(self.lawdata, "invalid hieralchy "+self.parent.__class__.__name__ + " -> " + self.__class__.__name__)
