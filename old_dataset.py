from sql.sql_deco import *
from sql import table_schema as ts
from operator import attrgetter
from threading import Thread
from collections import Counter

DEFAULT_TYPES = ["all", "prefecture", "municipality", "ordinance", "article", "paragraph"]
def _type_check(val, types=DEFAULT_TYPES):
	ptn = re.compile(val)
	for t in types:
		if ptn.match(t):
			return t

def del_paren(s):
	paren_match_dict = {"(": ")", "（": "）", "「": "」"}
	paren_stack = []
	ret = ""
	for c in s:
		# 左括弧はスタック
		if not paren_match_dict.get(c, None) is None:
			paren_stack.append(c)
		# スタックが空でない場合
		elif len(paren_stack) > 0:
			# 右括弧でスタックにマッチするならポップ
			if c == paren_match_dict[paren_stack[-1]]:
				paren_stack.pop()
			# 左括弧でスタックにマッチしないならエラー
			elif c in paren_match_dict.values():
				return None
		# スタックが空の場合
		else:
			# 左括弧でスタックにマッチしないならエラー
			if c in paren_match_dict.values():
				return None
			ret += c
	return ret


@db_deco
def get_dataset_name(cursor, root_type, root_id, unit_type):
	if root_type == "all":
		root_name = "日本"
	elif root_type in "prefecture municipality":
		res = cursor.execute("SELECT name FROM {0} WHERE code = ?;".format(root_type), (root_id,)).fetchone()
		if res is None:
			raise ValueError("invalid root_id "+str(root_id))
		elif root_type is "municipality" and root_id%10000 < 10:
			res = cursor.execute("SELECT name FROM prefecture WHERE code = ?;", (int(root_id/10000),)).fetchone()
			if res is None:
				raise ValueError("invalid root_id "+str(root_id))
			res = [res[0]+"(muni_ord)"]
		root_name = res[0]
	else:
		res = cursor.execute("SELECT name FROM {0} WHERE id = ?;".format(root_type), (root_id,)).fetchone()
		if res is None:
			raise ValueError("invalid root_id "+str(root_id))
		root_name = res[0]

	new_name_base = root_name+"_"+unit_type[0:4]
	new_name = new_name_base
	for i in range(999):
		if cursor.execute("SELECT id FROM dataset WHERE name = ?;", (new_name,)).fetchone() is None:
			return new_name
		new_name = new_name_base+"({0})".format(i)
	print("dataset name duplication error")
	raise

@db_deco
def get_dataset_id(cursor, root_type, root_id, unit_type):
	root_type = _type_check(root_type, ["all", "prefecture", "municipality", "ordinance", "article"])
	unit_type = _type_check(unit_type, ["prefecture", "municipality", "ordinance", "article", "paragraph"])
	
	res = cursor.execute("""
		SELECT id FROM dataset
		WHERE root_type = ?
		AND root_id = ?
		AND unit_type = ?;
		""", (root_type, root_id, unit_type)).fetchone()

	if res is not None:
		return res[0]

	dataset_name = get_dataset_name(root_type, root_id, unit_type)

	return cursor.execute("""
		INSERT INTO dataset(name, root_type, root_id, unit_type) VALUES (?, ?, ?, ?);
		SELECT id FROM dataset WHERE ROWID = last_insert_rowid();
		""", (dataset_name, root_type, root_id, unit_type)).fetchone()[0]

class Dataset(object):
	ID_STATEMENT = {
		"prefecture": "prefecture.code",
		"municipality": "municipality.code",
		"ordinance": "ordinance.id",
		"article": "article.id",
		"paragraph": "paragraph.id"
	}

	def __init__(self, root_type, root_id, unit_type):
		execute(ts.DATASET_TABLE)

		self.root_type = _type_check(root_type)
		self.root_id = 0 if self.root_type is "all" else root_id
		self.unit_type = _type_check(unit_type)
		self.dataset_id = get_dataset_id(self.root_type, self.root_id, self.unit_type)
		self.name = execute("SELECT name FROM dataset WHERE id = ?;", (self.dataset_id,)).fetchone()[0]
		self.thread = None
		self.vocab = None

	def vocab_info(self):
		if self.vocab is None:
			def _get_words():
				for tag, s in self.iter_dataset():
					for w in re.split(" ", s):
						yield w
			self.vocab = Counter(_get_words())
		return self.vocab

	def sentence_per_unit(self):
		scount = 0
		ucount = 0
		tadashi = 0
		for tag, s in self.iter_dataset():
			if s == "":
				continue
			if re.search("次(?:の各号)?に掲げる", s):
				print("-- sentence with items --")
				print(s)
				continue

			noparen_s = del_paren(s)
			if noparen_s is None:
				print("-- paren error --")
				print(self.search_data_name(tag))
				print(s)
				continue
			if "。 ただし" in noparen_s or "。 但し" in noparen_s:
				tadashi += 1
			scount += noparen_s.count("。")
			ucount += 1
		print(scount, "sentences")
		print("(", tadashi, "tadashi_gaki )")
		print(ucount, "units")
		print(float(scount) / float(ucount), "s/u")
		print("(", (float(scount) - float(tadashi))/ float(ucount), "s/u without tadashi_gaki )")


	def search_data_sentence(self, i):
		sentences = execute("""
				SELECT
				paragraph.sentence
				FROM ordinance
				INNER JOIN article ON article.ord_id = ordinance.id
				INNER JOIN paragraph ON paragraph.article_id = article.id
				WHERE {0} = ?
				ORDER BY article.num ASC, paragraph.num ASC
		""".format(self.ID_STATEMENT[self.unit_type]), (i,)).fetchall()
		return "".join(map(lambda x: x[0], sentences))

	def search_data_name(self, i, caption_flag=True, name_flag=True):
		if self.unit_type in "paragraph article":
			name, aid, pid, cap = execute("""
				SELECT
				ordinance.name,
				article.num,
				paragraph.num,
				article.caption
				FROM ordinance
				INNER JOIN article ON article.ord_id = ordinance.id
				INNER JOIN paragraph ON paragraph.article_id = article.id
				WHERE {0} = ?;
				""".format(self.ID_STATEMENT[self.unit_type]), (i,)).fetchone()
			if not caption_flag:
				cap = ""
			aid_str = str(int(aid/1000)) if aid % 1000 == 0 else "{0}_{1}".format(int(aid/1000), aid - (int(aid/1000)*1000))
			if self.unit_type is "paragraph":
				pid_str = str(int(pid/1000)) if pid % 1000 == 0 else "{0}_{1}".format(int(pid/1000), pid - (int(pid/1000)*1000))
				if name_flag:
					return "{0}_第{1}条_第{2}項{3}".format(name, aid_str, pid_str, cap)
				else:
					return "第{0}条_第{1}項{2}".format(aid_str, pid_str, cap)
			else:
				if name_flag:
					return "{0}_第{1}条{2}".format(name, aid_str, cap)
				else:
					return "第{0}条{1}".format(aid_str, cap)
		if name_flag:
			return execute("SELECT name FROM {0} WHERE {1} = ?;".format(self.unit_type, self.ID_STATEMENT[self.unit_type]), (i,)).fetchone()[0]
		return ""

	def get_index_list_all(self, order="RANDOM()"):
		if self.root_type is "all":
			c = execute("SELECT {0} FROM {1} ORDER BY {2};".format(self.ID_STATEMENT[self.unit_type], self.unit_type, order))
		else:
			c = execute(
			"""
			SELECT DISTINCT {0}
			FROM paragraph
			INNER JOIN article ON article.id = paragraph.article_id
			INNER JOIN ordinance ON ordinance.id = article.ord_id
			INNER JOIN municipality ON municipality.code = ordinance.muni_code
			INNER JOIN prefecture ON prefecture.code = municipality.pref_code
			WHERE {1} = ?
			ORDER BY {2};
			""".format(self.ID_STATEMENT[self.unit_type], self.ID_STATEMENT[self.root_type], order), 
			(self.root_id,)
			)
		return [ret[0] for ret in c]

	def parse_data_name(self, name, num_as_integer=False):
		m = re.match("(?P<ordinance_name>[^_]+(?:条例|規則))(?:_第(?P<article_num>[0-9_]+)条)?(?:_第(?P<paragraph_num>[0-9_]+)項)?(?P<caption>\(.+?\))?$", name)
		ret = m.groupdict(default=None)
		if num_as_integer:
			if ret["article_num"] is not None:
				try:
					ret["article_num"] = int(ret["article_num"])*1000
				except:
					anum1, anum2 = re.split("_", ret["article_num"])
					ret["article_num"] = int(anum1)*1000 + int(anum2)
			if ret["paragraph_num"] is not None:
				try:
					ret["paragraph_num"] = int(ret["paragraph_num"])*1000
				except:
					pnum1, pnum2 = re.split("_", ret["paragraph_num"])
					print(pnum1, pnum2)
					ret["paragraph_num"] = int(pnum1)*1000 + int(pnum2)
		return ret

	def get_index_from_name(self, name):
		parsed_name = self.parse_data_name(name, num_as_integer=True)
		#set_tracer()
		statement = "\n".join(["""
		SELECT DISTINCT 
		{0} as unit_id,
		ordinance.name as ordinance_name,
		article.num as article_num,
		paragraph.num as paragraph_num
		FROM paragraph
		INNER JOIN article ON article.id = paragraph.article_id
		INNER JOIN ordinance ON ordinance.id = article.ord_id
		INNER JOIN municipality ON municipality.code = ordinance.muni_code
		INNER JOIN prefecture ON prefecture.code = municipality.pref_code
		WHERE ordinance_name = :ordinance_name""".format(self.ID_STATEMENT[self.unit_type],),
		"AND article_num = :article_num" if parsed_name["article_num"] is not None else "",
		"AND paragraph_num = :paragraph_num" if parsed_name["paragraph_num"] is not None else "",
		";"
		])
		c = execute(statement, parsed_name).fetchone()
		if c is None:
			return None
		return c[0]

	def iter_dataset(self, order="RANDOM()", index_list=None):
		self.job_queue = Queue(30000)
		self.res_queue = Queue(30000)

		if index_list is None:
			index_list = self.get_index_list_all(order=order)

		@exec_process(self.job_queue, self.res_queue)
		@db_deco
		def _iter_dataset(cursor, job_queue, index_list):
			#root_type, root_id, unit_type = cursor.execute("SELECT root_type, root_id, unit_type WHERE id = ?", dataset_id)
			print("dataset iteration thread")
			for unit_id in index_list:
				job_queue.put(
				("""
				SELECT
				{0},
				paragraph.sentence
				FROM paragraph
				INNER JOIN article ON article.id = paragraph.article_id
				INNER JOIN ordinance ON ordinance.id = article.ord_id
				INNER JOIN municipality ON municipality.code = ordinance.muni_code
				INNER JOIN prefecture ON prefecture.code = municipality.pref_code
				WHERE {0} = ?
				ORDER BY prefecture.code ASC, municipality.code ASC, ordinance.num ASC, article.num ASC, paragraph.num ASC;
				""".format(self.ID_STATEMENT[self.unit_type]), (unit_id,), 'fetchall'))
			print("send all sql")
		thread = Thread(target=_iter_dataset, kwargs={"index_list":index_list}, daemon=True)
		thread.start()
		print("iter start")
		counters = 0
		while True:
			q = self.res_queue.get()
			if q is None:
				break
			if len(q) == 0:
				continue
			try:
				i = q[0][0]
			except:
				print(q)
				raise
			s = " ".join((s for _, s in q))
			counters += 1
			yield i, s
		print("iter finish")
		print("yielded {0} units".format(counters))
		print("join thread")
		del self.job_queue
		del self.res_queue
		raise StopIteration

	def collect_units(self, qid, qid_type="ordinance"):
		#set_tracer()
		ret = [i for i, in execute("""
				select {0} from paragraph
				inner join article on paragraph.article_id = article.id
				inner join ordinance on ordinance.id = article.ord_id
				where {1} = ?
				and paragraph.num > 0
				ORDER BY article.num ASC, paragraph.num ASC;
				""".format(self.ID_STATEMENT[self.unit_type], self.ID_STATEMENT[qid_type]), (qid,))]
		return ret

if __name__ == "__main__":
	dataset = Dataset(root_type="municipality", root_id=230006, unit_type="paragraph")
	print(dataset.sentence_per_unit(), "s/u")
	#set_tracer()
	# set_db_path("/Users/KazuyaFujioka/Documents/fd2v/dbfile/LawInfoDB_AP_FK.db")
	# execute("DROP TABLE dataset;")
	# sample_id, = execute("SELECT id FROM ordinance ORDER BY RANDOM();").fetchone()
	# print(sample_id)
	# dataset = Dataset(root_type="ordinance", root_id=sample_id, unit_type="article")
	
	# for i, s in dataset.iter_dataset():
	# 	print(i, s[0:20])
	# 	pass

	# for i, s in dataset.iter_dataset():
	# 	print(i, s[0:20])
	# 	pass

	# for i, s in dataset.iter_dataset():
	# 	print(i, s[0:20])
	# 	pass







