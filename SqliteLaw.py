from LawAbstCls import LawAbstCls
from AsyncSqlite import MyApswConnection
from SqliteLawElements import Root

class SqliteLaw(LawAbstCls):
	@property
	def oid(self):
		if "_oid" not in self.__dict__:
			self._oid = None
		return self._oid

	@oid.setter
	def oid(self, i):
		self._oid = i

	def load_from_db(self, ident, dbfile):
		assert self.root is None
		self.dbfile = dbfile
		self.conn = MyApswConnection(dbfile)
		self.oid = ident
		self.file_code, self.municipality_code, self.prefecture_code = self.conn.conn.cursor().execute("""
			SELECT
			ordinances.file_id as fid,
			ordinances.muni_id as mid,
			municipalities.pref_id as pid
			FROM ordinances
			INNER JOIN municipalities ON municipalities.id = mid
			WHERE ordinances.id = ?;
		""", (self.oid,)).fetchone()
		self.root = Root(self)

	def _get_law_name(self):
		self.conn.execute("SELECT name FROM ordinance WHERE id = ?")

	def _get_law_num(self):
		self.conn.execute("SELECT num FROM ordinance WHERE id = ?")

if __name__ == '__main__':
	ld = SqliteLaw()
	ld.load_from_db(1, "./test.db")
	for s in ld.iter_sentences():
		print(s)
