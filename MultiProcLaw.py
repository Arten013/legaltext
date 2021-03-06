from collections import Counter
import asyncio
import concurrent.futures
import PostgresTables as ts

if __name__ == "__main__":
    from TextIO import kansuji2arabic as kan_ara, find_all_files
    from PostgresLaw import PostgresLaw
    from PostgresRegisterMethod import PostgresRegisterMethod
    from LawError import *
    from EtreeLaw import EtreeLaw
    from EType import BASIC_ETYPE_SET
    import asyncpg
else:
    from .TextIO import kansuji2arabic as kan_ara
    from .PostgresLaw import PostgresLaw
    from .PostgresRegisterMethod import PostgresRegisterMethod
    from .LawError import *
    from .EtreeLaw import EtreeLaw

PARENT_CLASSES = [EtreeLaw, PostgresLaw, PostgresRegisterMethod]
class Law(*PARENT_CLASSES):
    async def register(self, conn=None, string_table_flag=False):
        conn = self.conn if conn is None else conn

        # 読み込みしてない場合はraise
        if self.root is None:
            raise ValueError("You must load source ordinance file before registration.")
        
        # 登録済みの場合
        self.oid = await self.search_oid(conn)
        if self.oid is not None:
            print("skip (already registered): ", self.name)
            return

        # 未登録の場合
        # 本体の登録            
        try_count = 0
        while True:
            await self.transaction_begin(conn)
            try_count += 1
            try:
                await self.register_law(conn)
                self.oid = await self.search_oid(conn)

                # LawElementsの登録
                async for elem in self.root.async_iter_descendants():
                    await self.register_elements(conn, elem)
                    elem.id = await self.search_elements(conn, elem)

                    # stringを別登録する場合
                    if string_table_flag:
                        for snum, text in enumerate(elem.texts):
                            sid = await self.search_string(conn, text)
                            if sid is None:
                                await self.register_string(conn, text)
                                sid = await self.search_string(conn, text)
                            await self.register_string_edge(conn, elem, sid, snum)
                await self.transaction_end(rollback=False)
                print("commit:", self.name)
                return self
            except LawError as e:
                await self.transaction_end(rollback=True)
                print("rollback:", self.name)
                raise
                return None
            except:
                await self.transaction_end(rollback=True)
                if try_count <= 3:
                    print("retry:", self.name)
                    continue
                print("rollback:", self.name)
                raise
                return None

              

async def get_lawdata(path, usr, db):
    try:
        ld = Law()
        ld.load_from_path(path)
        await ld.async_connect(user=usr, database=db)
        return ld
    except:
        raise
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

async def init_tables(conn, csv_path, loop=None):
    loop = asyncio.get_event_loop() if loop is None else loop
    await conn.execute(ts.PREF_TABLE+ts.MUNI_TABLE+ts.ORD_TABLE+ts.ELEMENTS_TABLE+ts.STRINGS_TABLE+ts.STRING_EDGES_TABLE)
    with open(csv_path) as f:
        reader = csv.reader(f)
        mc2pc = lambda mc: int(int(mc)/10000)
        next(reader)
        prefectures = dict()
        municipalities = []
        for mc, pn, mn, _, _ in reader:
            prefectures[pn] = mc2pc(mc)
            municipalities.append([int(mc), mc2pc(mc), mn])
    async with conn.transaction():
        for pn, pc in prefectures.items():
            await conn.execute("INSERT INTO prefectures(id, name) VALUES($1, $2);", pc, pn)
        for args in municipalities:
            await conn.execute("INSERT INTO municipalities(id, pref_id, name) VALUES($1, $2, $3)", *args)



if __name__ == '__main__':
    import os
    import csv
    import glob
    import re

    TEST_DB = "ordinance"
    TEST_USER = "KazuyaFujioka"

    #os.remove(TEST_DBFILE)
    async def test_init():
        GOV_PATH = os.path.join(os.path.dirname(__file__), "municode.csv")
        conn = await asyncpg.connect(user=TEST_USER, database=TEST_DB)
        for t in ["prefectures", "municipalities", "ordinances", "elements", "strings", "string_edges"][::-1]:
            f = await conn.fetchval("SELECT 1 FROM pg_stat_user_tables WHERE relname = $1;", t)
            if f is not None:
                await conn.execute("DROP TABLE {};".format(t))
        await init_tables(conn, GOV_PATH)
        await conn.close()

    #loop = asyncio.get_event_loop()
    #loop.run_until_complete(test_init())

    def register_reikis_from_directory(path, db, user):
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()

        async def register(path, db, user, string_table_flag):
            l = await Law().async_load_from_path(path)
            if l is None:
                print("skip (load failure): ", l.name)
                return
            if not l.is_reiki():
                print("skip (not reiki): ", l.name)
                return
            try:
                await l.async_connect(user=user, database=db)
                await l.register(string_table_flag=string_table_flag)
            except Exception as e:
                print("Exception: ", str(e))
                raise
            finally:
                if "conn" in l.__dict__:
                    await l.async_close()

        async def reg_from_path(path, db, user):
            loop = asyncio.get_event_loop()
            laws = []
            futures = []
            load_futures = []
            loading_laws = []
            for path in find_all_files(path, [".xml"]):
                futures.append(register(path, db, user, string_table_flag=True))
                if len(futures) >= 10:
                    await asyncio.wait(futures)
                    futures = []

        print("run")
        f = asyncio.ensure_future(reg_from_path(path, db, user))
        loop.run_until_complete(f)
        print("end")
        return f.result()

        """
        async def enqueue(q, e, path):
            loop = asyncio.get_event_loop()
            for path in find_all_files(path, [".xml"]):
                l = await Law().async_load_from_path(path)
                await q.put(l)
            e.set()
            print("ENQUEUE FINISH")
            q.join()

        async def dequeue(q, e, db, user):
            loop = asyncio.get_event_loop()
            while True:
                try:
                    l = await asyncio.wait_for(q.get(), 0.1)
                except asyncio.TimeoutError:
                    print("TIMEOUT:", l)
                    if q.empty() and e.is_set():
                        #await q.join()
                        break
                    continue
                await register(l, db, user, string_table_flag=True)
                q.task_done()
                #if len(futures) >= 1:
                #    await asyncio.wait(futures)
                #    futures = []
            print("DEQUEUE FINISH")
        """
        #q = asyncio.Queue(10)
        #e = asyncio.Event()
        #f = asyncio.wait([enqueue(q, e, path)] + [dequeue(q, e, db, user)] * 5)


    def register_all(path, db, user):
        c = Counter()
        error_count = 0
        reiki_count = 0
        loop = asyncio.get_event_loop()
        #i = 0
        futures = []
        with concurrent.futures.ProcessPoolExecutor(4) as e:
            for p in glob.iglob(path+"**", recursive=True):
                if re.match("\d{6}", os.path.split(p)[1]):
                    futures.append(loop.run_in_executor(e, register_reikis_from_directory, p, db, user))
                #if len(futures) >= 10:
                #    break
            loop.run_until_complete(asyncio.wait(futures))

    """
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
    """
    #register_reikis_from_directory("/Users/KazuyaFujioka/Documents/all_data/23/230006", TEST_DB, TEST_USER)
    from time import time
    t1 = time()
    register_all("/Users/KazuyaFujioka/Documents/all_data/", TEST_DB, TEST_USER)
    print("time: ", time()-t1)
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
