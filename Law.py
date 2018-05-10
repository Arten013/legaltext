from EtreeLaw import EtreeLaw
from SqliteLaw import SqliteLaw
from collections import Counter
import asyncio
from LawError import *
from concurrent.futures import ThreadPoolExecutor
import apsw
from SqliteRegisterMethods import SqliteRegisterMethods
from PostgresLaw import PostgresLaw
from PostgresRegisterMethods import PostgresRegisterMethods

if __name__ != "__main__":
    from .TextIO import kansuji2arabic as kan_ara
    from .SqliteTables import *

PARENT_CLASSES = [EtreeLaw, PostgresLaw, PostgresRegisterMethods]
class Law(*PARENT_CLASSES):
    async def register(self, conn=None, string_table_flag=False):
        conn = self.conn if conn is None else conn

        # 読み込みしてない場合はraise
        if self.root is None:
            raise ValueError("You must load source ordinance file before registration.")
        
        # 登録済みの場合
        self.oid = await self.search_oid(conn)
        if self.oid is not None:
            print("already registered: ", self.name)
            return

        # 未登録の場合
        # 本体の登録
        await self.register_law(conn)
        self.oid = await self.search_oid(conn)
        await self.register_decendants(conn)

        # LawElementsの登録
        for elem in self.root.iter_descendants():
            await self.register_elements(conn, elem)
            elem.id = await self.search_elements(conn, elem)

            # stringを別登録する場合
            if string_table_flag:
                for snum, text in enumerate(elem.texts):
                    sid = await self.search_string(conn, text)
                    if sid is None:
                        await self.register_string(conn, text)
                        sid = await self.search_string(conn, text)
                    await self.register_string_edge(conn, text, sid, snum)

        print("reg:", self.name)
        return self
              

def get_lawdata(path):
    try:
        ld = Law()
        ld.load_from_path(path)
        return ld
    except:
        return None

def fill_ap_table(path_list):
    # カウンター
    file_count = 0
    err_count = 0
    elem_counter = Counter()
    def mecab_preprocess(self, s):
        return " ".join(list(Morph(s))[1:-1])
    Law.preprocess = mecab_preprocess
    # dbへの登録
    with Pool(PROC_NUM) as p:
        # Lawの取得（マルチプロセス） & イテレーション
        for l in p.imap(Law, path_list):
            file_count += 1
            if l is None:
                err_count += 1
                continue
            print(l.path)
            elem_counter.update(l.count_elems())
            if not l.is_reiki:
                err_count += 1
                continue
            l.reg_db()
    print("Extracted {0} files ({1} error raised)".format(file_count, err_count))
    print("Registered {0} articles and {1} paragraphs".format(article_count, paragraph_count))

def init_gov_tables(conn, csv_path):
    with open(csv_path) as f:
        reader = csv.reader(f)
        mc2pc = lambda mc: int(int(mc)/10000)
        next(reader)
        gen = ([mc2pc(mc), pn, int(mc), mc2pc(mc), mn] for mc, pn, mn, _, _ in reader)
        conn.conn.cursor().executemany("REPLACE INTO prefectures VALUES(?, ?); INSERT INTO municipalities VALUES(?, ?, ?)", gen)

def init_tables(conn):
    loop = asyncio.get_event_loop()
    loop.run_until_complete( conn.execute(ts.PREF_TABLE+ts.MUNI_TABLE+ts.ORD_TABLE+ts.ELEMENTS_TABLE))


if __name__ == '__main__':
    from TextIO import kansuji2arabic as kan_ara, find_all_files
    from SqliteTables import *
    from LawElementBase import BASIC_ETYPE_SET
    import AsyncSqlite as asq
    import os
    import csv
    import SqliteTables as ts
    import glob
    import re

    TEST_DBFILE = "./test.db"

    #os.remove(TEST_DBFILE)
    GOV_PATH = os.path.join(os.path.dirname(__file__), "municode.csv")
    conn = asq.MyApswConnection(TEST_DBFILE)
    #conn.set_exectracer(asq._exec_tracer)
    #conn.set_rowtracer(asq._row_tracer)
    init_tables(conn)
    #conn.conn.close()
    #init_gov_tables(conn, GOV_PATH)

    def register_reikis_from_directory(path, conn):
        loop = asyncio.get_event_loop()
        #conn.set_exectracer(asq._exec_tracer)
        #conn.set_rowtracer(asq._row_tracer)
        async def fgather(*futures):
            done, pending = await asyncio.wait(futures)
            print("done:", len(done), "pend", len(pending))
            for d in done:
                try:
                    print("reg:", d.result())
                except Exception as e:
                    print(str(e))
        def _path_proc(root, dirs, files, extentions):
            if extentions is None or os.path.splitext(root)[1] in extentions:
                    yield root
            for file in files:
                if extentions is None or os.path.splitext(file)[1] in extentions:
                    yield os.path.join(root, file)

        def enqueue_all_files(directory, extentions=None):
            #print(directory)
            executor = ThreadPoolExecutor(1)
            loop = asyncio.get_event_loop()
            futures = []
            for root, dirs, files in os.walk(directory):
                yield loop.run_in_executor(executor, _path_proc, root, dirs, files, extentions)

        async def reg_from_path(path):
            loop = asyncio.get_event_loop()
            laws = []
            for pf in enqueue_all_files(path, [".xml"]):
                futures = []
                await conn.connect()
                await asyncio.wait([pf])
                for path in pf.result():
                    l = get_lawdata(path)
                    if l is None:
                        continue
                    if not l.is_reiki():
                        continue
                    #print(l)
                    future = asyncio.ensure_future(l.register(conn))
                    #f.set_exception(LawError(l))
                    futures.append(future)
                    laws.append(l)
                await fgather(*futures)
                await conn.close()
            return laws

        print("run")
        f = asyncio.ensure_future(reg_from_path(path))
        loop.run_until_complete(f)
        print("end")
        return f.result()

    def register_all(path, conn):
        c = Counter()
        error_count = 0
        reiki_count = 0
        loop = asyncio.get_event_loop()
        #i = 0
        for p in glob.iglob(path+"**", recursive=True):    
            if re.match("\d{6}", os.path.split(p)[1]):
                ll = register_reikis_from_directory(p, conn)
                for l in ll:
                    try:
                        c.update(l.count_elems())
                        reiki_count += 1
                    except LawError as e:
                        error_count += 1
                        continue
                #i += 1
                #if i > 1:
                #   break
        print("reiki_count:", reiki_count)
        print("error_count:", error_count)
        print()
        print("-- structure counts --")
        for ename in BASIC_ETYPE_SET:
            print(ename, c[ename])

    #register_reikis_from_directory("/Users/KazuyaFujioka/Documents/all_data/23/230006/")
    register_all("/Users/KazuyaFujioka/Documents/all_data/", conn)
    #ll = [get_lawdata("/Users/KazuyaFujioka/Documents/all_data/23/230006/{0:04}.xml".format(i)) for i in range(1,100)]
    #l1 = get_lawdata("/Users/KazuyaFujioka/Documents/all_data/23/230006/0001.xml")
    #l2 = get_lawdata("/Users/KazuyaFujioka/Documents/all_data/23/230006/0002.xml")
    #loop = asyncio.get_event_loop()
    #futures = []
    #for l in ll:
    #    future = asyncio.ensure_future(l.register(conn))
    #    future.add_done_callback(lambda x: print("done"))
    #    futures.append(future)
    #future = asyncio.ensure_future(l2.register(conn))
    #loop.run_until_complete(asyncio.wait(futures))
"""
    loop = asyncio.get_event_loop()
    # Lawの取得（マルチプロセス） & イテレーション
    with concurrent.futures.ThreadPoolExecutor() as executor:
        await self.loop.run_in_executor(executor, cursor.execute, statement, bindings)
            for l in map(get_lawdata, find_all_files("/Users/KazuyaFujioka/Documents/all_data/23/230006", [".xml"])):
                if l is None or not l.is_reiki():
                    continue
                reiki_count += 1
                try:
                    c.update(l.count_elems())
                    future = asyncio.ensure_future(l.register(conn))
                    loop.run_until_complete(future)
                    print("reg", l)
                except LawError as e:
                    error_count += 1
                    print(e)
                    continue
        #for s in l.iter_sentences():
"""
