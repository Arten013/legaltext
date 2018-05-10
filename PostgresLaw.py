from LawAbstCls import LawAbstCls
from PostgresLawElement import Root
from concurrent.futures import ThreadPoolExecutor

import asyncio
import asyncpg


class PostgresLaw(LawAbstCls):
    @property
    def oid(self):
        if "_oid" not in self.__dict__:
            self._oid = None
        return self._oid

    @oid.setter
    def oid(self, i):
        self._oid = i

    def connect(self, *args, **kwargs):
        self.loop = asyncio.get_event_loop()
        self.conn = self.loop.run_until_complete(asyncpg.connect(*args, **kwargs))
        self.executor = ThreadPoolExecutor(10)

    async def execute(self, *args, **kwargs):
        return await self.loop.run_in_executor(self.executor, self.conn.execute, *args, **kwargs)

    async def fetch(self, *args, **kwargs):
        return await self.loop.run_in_executor(self.executor, self.conn.fetch, *args, **kwargs)

    async def fetchval(self, *args, **kwargs):
        return await self.loop.run_in_executor(self.executor, self.conn.fetchval, *args, **kwargs)

    async def fetchrow(self, *args, **kwargs):
        return await self.loop.run_in_executor(self.executor, self.conn.fetchrow, *args, **kwargs)

    def load_from_db(self, ident, conn):
        assert self.root is None
        self.conn = conn
        self.oid = ident
        f = self.fetchrow("""
            SELECT
            ordinances.file_id as file_code,
            ordinances.muni_id as municipality_code,
            municipalities.pref_id as prefecture_code
            FROM ordinances
            INNER JOIN municipalities ON municipalities.id = municipality_code
            WHERE ordinances.id = $1;
        """, self.oid))
        self.loop.run_until_complete(f)
        self.__dict__.update(f.result())
        self.root = Root(self)

    def _get_law_name(self):
        self.conn.execute("SELECT name FROM ordinance WHERE id = $1", self.oid)

    def _get_law_num(self):
        self.conn.execute("SELECT num FROM ordinance WHERE id = $1", self.oid)

if __name__ == '__main__':
    import PostgresTables as ts

    ld = PostgresLaw()
    ld.connect(user="KazuyaFujioka", database="ordinance")
    asyncio.get_event_loop().run_until_complete(ld.conn.execute(ts.PREF_TABLE+ts.MUNI_TABLE+ts.ORD_TABLE))
