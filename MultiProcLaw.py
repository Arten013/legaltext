from collections import Counter
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
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
            print("already registered: ", self.name)
            return

        # 未登録の場合
        # 本体の登録            
        await self.transaction_begin(conn)
        try:
            await self.register_law(conn)
            self.oid = await self.search_oid(conn)

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
            await self.transaction_end()
            print("commit:", self.name)
            return self
        except:
            await self.transaction_end(rollback=True)
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
    await conn.execute(ts.PREF_TABLE+ts.MUNI_TABLE+ts.ORD_TABLE+ts.ELEMENTS_TABLE)
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
        await conn.execute("DROP TABLE prefectures, ordinances, municipalities, elements;")
        await init_tables(conn, GOV_PATH)
        await conn.close()

    loop = asyncio.get_event_loop()
    #loop.run_until_complete(test_init())

    def register_reikis_from_directory(path, db, user):
        loop = asyncio.get_event_loop()

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

        async def register(l, db, user):
            try:
                await l.async_connect(user=user, database=db)
                await asyncio.ensure_future(l.register())
                ret = l
            except Exception as e:
                print(str(e))
                ret = None
            finally:
                if "conn" in l.__dict__:
                    await l.async_close()
                return ret

        async def reg_from_path(path, db, user):
            loop = asyncio.get_event_loop()
            laws = []
            with ThreadPoolExecutor(3) as executor:
                for pf in enqueue_all_files(path, [".xml"]):
                    futures = []
                    load_futures = []
                    loading_laws = []
                    await asyncio.wait([pf])
                    for path in pf.result():
                        l = Law()
                        load_futures.append(loop.run_in_executor(executor, l.load_from_path, path))
                        loading_laws.append(l)
                    for f, l in zip(load_futures, loading_laws):
                        await f
                        if not l.is_reiki():
                            continue
                        print(l)
                        futures.append(register(l, db, user))
                    laws.extend(await asyncio.wait(futures))
            return laws

        print("run")
        f = asyncio.ensure_future(reg_from_path(path, db, user))
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

    register_reikis_from_directory("/Users/KazuyaFujioka/research/legaltext/testset/23/230006", TEST_DB, TEST_USER)
    #register_all("/Users/KazuyaFujioka/Documents/all_data/", conn)
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
