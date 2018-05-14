import re
from LawError import *
from LawElement import *
from EType import ETYPES, ETYPES_DICT
from decimal import Decimal
from xml.etree.ElementTree import Element
from LawElementNumber import LawElementNumber
#from mojimoji import zen_to_han
import asyncio
import concurrent.futures

get_text = lambda b, e_val: b.text if b is not None and b.text else e_val

class ETreeLawElementBase(LawElementBase):
    def inheritance(self, root):
        self.root = root
        super().inheritance()

    def _iter_possible_children(self):
        for f in self.root.findall("./*"):
            if f.tag not in ETYPES:
                continue
            child = globals()[f.tag](lawdata=self.lawdata, parent=self)
            child.inheritance(f)
            yield child

    async def _async_iter_possible_children(self):
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor(1) as e:
            future = await loop.run_in_executor(e, self.root.findall, "./*")
        for f in future:
            if f.tag not in ETYPES:
                continue
            child = globals()[f.tag](lawdata=self.lawdata, parent=self)
            child.inheritance(f)
            yield child

    def get_number(self):
        try:
            return LawElementNumber(self.etype, self.root)
        except LawElementNumberError as e:
            raise LawElementNumberError(self.lawdata, **e.__dict__)

class Root(RootBase, ETreeLawElementBase):
    def _iter_possible_children(self):
        for f in self.root.findall("Law/LawBody/*"):
            if f.tag not in ETYPES:
                continue
            child = globals()[f.tag](lawdata=self.lawdata, parent=self)
            child.inheritance(f)
            yield child

    async def _async_iter_possible_children(self):
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor(1) as e:
            future = await loop.run_in_executor(e, self.root.findall, "Law/LawBody/*")
        for f in future:
            if f.tag not in ETYPES:
                continue
            child = globals()[f.tag](lawdata=self.lawdata, parent=self)
            child.inheritance(f)
            yield child

    def get_law_name(self):
        return get_text(self.root.find('Law/LawBody/LawTitle'), 'UNK')
        
    def get_law_num(self):
        raw_text = get_text(self.root.find('Law/LawNum'), 'UNK')
        if raw_text is None:
            return None
        #tmp = zen_to_han(raw_text, kana=False, ascii=False)
        tmp = raw_text
        re.sub("\s", "", tmp)
        text = kan_ara(tmp)
        return text

class MainProvision(ProvBase, ETreeLawElementBase):
    pass

class SupplProvision(ProvBase, ETreeLawElementBase):
    pass

class Part(SuperordinateElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (MainProvision,)

class Chapter(SuperordinateElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (MainProvision, Part)

class Section(SuperordinateElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (Chapter,)

class Subsection(SuperordinateElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (Section,)

class Division(SuperordinateElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (Subsection,)

class Article(BasicElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (MainProvision, SupplProvision, Part, Chapter, Section, Subsection, Division)

class ETreeSentenceBase(SentenceBase, ETreeLawElementBase):
    def inheritance(self, root):
        self.root = root
        self.texts = self.extract_text()

    def extract_text(self):
        return list(get_text(s, "") for s in self.root.findall('./Sentence'.format(self.__class__.__name__)))

class ArticleCaption(CaptionBase, ETreeSentenceBase):
    PARENT_CANDIDATES = (Article,)
    def extract_text(self):
        return [get_text(self.root, '')]

class Paragraph(BasicElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (MainProvision, SupplProvision, Article)

class ParagraphSentence(ETreeSentenceBase):
    PARENT_CANDIDATES = (Paragraph,)

class Item(ItemBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (Article, Paragraph)

class ItemSentence(ETreeSentenceBase):
    PARENT_CANDIDATES = (Item,)

class Subitem1(Item):
    PARENT_CANDIDATES = (Item,)

class Subitem1Sentence(ItemSentence):
    PARENT_CANDIDATES = (Item,)

class Subitem2(Item):
    PARENT_CANDIDATES = (Subitem1,)

class Subitem2Sentence(ItemSentence):
    PARENT_CANDIDATES = (Subitem1,)

class Subitem3(Item):
    PARENT_CANDIDATES = (Subitem2,)

class Subitem3Sentence(ItemSentence):
    PARENT_CANDIDATES = (Subitem2,)

class Subitem4(Item):
    PARENT_CANDIDATES = (Subitem3,)

class Subitem4Sentence(ItemSentence):
    PARENT_CANDIDATES = (Subitem3,)

class Subitem5(Item):
    PARENT_CANDIDATES = (Subitem4,)

class Subitem5Sentence(ItemSentence):
    PARENT_CANDIDATES = (Subitem4,)

