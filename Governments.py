from TextIO import find_all_files

class GovernmentBase(object):
    def __init__(self, path):
        self.path = path
        self._type = None
        self._code = None
        self._children = None

    def iter_children(self):
        yield from self.children

    @property
    def children(self):
        if self._children

    @property
    def code(self):
        if self._code is None:
            self._code = os.path.split(self._type)[1]
        return self._code

    @property
    def code_type(self):
        if self._code_type is None:
            if re.match("\d{2}$", self.code):
                self._code_type = "Prefecture"
            elif re.match("\d{6}$", self.code):
                self._code_type = "Municipality"
            else:
                self._code_type = "UNK"
        return self._code_type

class Prefecture(GovernmentBase):
    def __init__(self, path):
        super().__init__(path)
        self.parent_code = os.path.split(os.path.split(self.path)[0])[1]

    def iter_children(self):
        for p in glob.glob(os.path.join(self.path, "*")):





class Municipality(GovernmentBase):
    def __init__(self, path):
        super().__init__(path)
        self.parent_code = os.path.split(os.path.split(self.path)[0])[1]

class GovGroup(object):
    def __init__(self, rootpath):
        self.rootpath
        self.govs = {"Prefecture":{}, "Municipality"{}}

    def add_gov(self, code):
        if code not in self.govs:
            g = Government(os.path.join(self.rootpath, code))
            if g.type is not "UNK":
                self.govs[g.type][code] = g

    def init_gov_tables(self, conn, csv_path):
        with open(csv_path) as f:
            reader = csv.reader(f)
            mc2pc = lambda mc: int(int(mc)/10000)
            next(reader)
            gen = ([mc2pc(mc), pn, int(mc), mc2pc(mc), mn] for mc, pn, mn, _, _ in reader)
            conn.conn.cursor().executemany("REPLACE INTO prefectures VALUES(?, ?); INSERT INTO municipalities VALUES(?, ?, ?)", gen)


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