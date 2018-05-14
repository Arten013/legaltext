import re
from LawError import *
from LawElementBase import *
from LawElement import *
from LawElementNumber import LawElementNumber

class SqliteLawElementBase(LawElementBase):
    FIND_CHILDREN_STATEMENT = """
        SELECT id, etype, num
        FROM elements
        WHERE parent_id = ?
        ORDER BY num ASC;
    """

    def inheritance(self, i, num):
        self.conn = self.parent.conn
        self.id = i
        self.num = LawElementNumber(self.etype, num)

    def _iter_possible_children(self):
        for i, etype, num in self.lawdata.execute(self.FIND_CHILDREN_STATEMENT, (self.id,)):
            child = globals()[etype](lawdata=self.lawdata, parent=self)
            #print("hoge", i, num, child.__class__.__name__)
            child.inheritance(i, num)
            yield child

    async def _async_iter_possible_children(self):
        async for i, etype, num in self.lawdata.conn.fetchrow(self.FIND_CHILDREN_STATEMENT, self.id):
            child = globals()[etype](lawdata=self.lawdata, parent=self)
            #print("hoge", i, num, child.__class__.__name__)
            child.inheritance(i, num)
            yield child

    def _check_child(self, *args, **kwargs):
        return True

    def get_number(self):
        return self._num

class Root(RootBase, SqliteLawElementBase):
    FIND_CHILDREN_STATEMENT = """
        SELECT id, etype
        FROM elements
        WHERE ord_id = ?
        AND (etype='MainProvision' OR etype='SupplProvision')
        ORDER BY num ASC;
    """

    def __init__(self, lawdata, parent=None):
        super().__init__(lawdata, parent)
        self.conn = self.lawdata.conn

    def _iter_possible_children(self):
        for i, etype in self.conn.conn.cursor().execute(self.FIND_CHILDREN_STATEMENT, (self.lawdata.oid,)):
            child = globals()[etype](lawdata=self.lawdata, parent=self)
            child.inheritance(i, "0")
            yield child

    async def _async_iter_possible_children(self):
        async for i, etype, num in self.lawdata.conn.fetchrow(self.FIND_CHILDREN_STATEMENT, (self.lawdata.oid,)):
            child = globals()[etype](lawdata=self.lawdata, parent=self)
            child.inheritance(i, "0")
            yield child

    def get_law_name(self):
        try:
            return self.conn.conn.cursor().execute("SELECT name FROM ordinances WHERE id = ?", (self.lawdata.oid,)).fetchone()[0]
        except:
            return None

    def get_law_num(self):
        try:
            return LawElementNumber(self.etype, self.conn.conn.cursor().execute("SELECT num FROM ordinances WHERE id = ?", (self.lawdata.oid,)).fetchone()[0])
        except:
            return None

class SqlProvBase(ProvBase, SqliteLawElementBase):
    pass

class MainProvision(SqlProvBase):
    pass

class SupplProvision(SqlProvBase):
    pass

class Part(SuperordinateElementBase, SqliteLawElementBase):
    pass

class Chapter(SuperordinateElementBase, SqliteLawElementBase):
    pass

class Section(SuperordinateElementBase, SqliteLawElementBase):
    pass

class Subsection(SuperordinateElementBase, SqliteLawElementBase):
    pass

class Division(SuperordinateElementBase, SqliteLawElementBase):
    pass

class Article(BasicElementBase, SqliteLawElementBase):
    pass

class SqlSentenceBase(SentenceBase, SqliteLawElementBase):
    def inheritance(self, i, num):
        self.conn = self.parent.conn
        self.id = i
        self.num = LawElementNumber(self.etype, num)
        self.texts = self.extract_text()

    def extract_text(self):
        return [self.conn.conn.cursor().execute("SELECT content FROM elements WHERE id = ?", (self.id,)).fetchone()[0]]

class ArticleCaption(CaptionBase, SqlSentenceBase):
    pass

class Paragraph(BasicElementBase, SqliteLawElementBase):
    pass

class ParagraphSentence(SqlSentenceBase):
    pass

class Item(ItemBase, SqliteLawElementBase):
    pass

class ItemSentence(SqlSentenceBase):
    pass

class Subitem1(Item):
    pass

class Subitem1Sentence(ItemSentence):
    pass

class Subitem2(Item):
    pass

class Subitem2Sentence(ItemSentence):
    pass

class Subitem3(Item):
    pass

class Subitem3Sentence(ItemSentence):
    pass

class Subitem4(Item):
    pass

class Subitem4Sentence(ItemSentence):
    pass

class Subitem5(Item):
    pass

class Subitem5Sentence(ItemSentence):
    pass