from LawAbstCls import LawAbstCls
from PostgresLawElement import Root
from concurrent.futures import ThreadPoolExecutor

import asyncio
import asyncpg


class PostgresLaw(LawAbstCls):
    conn_counter = 0

    @property
    def identifier(self):
        return self.oid

    @property
    def oid(self):
        if "_oid" not in self.__dict__:
            self._oid = None
        return self._oid

    @oid.setter
    def oid(self, i):
        self._oid = i

    @property
    def loop(self):
        if "loop" not in self.__dict__:
            self.loop = asyncio.get_event_loop()

    async def async_close(self):
        assert self.conn is not None
        await self.conn.close()

    def connect(self, *args, **kwargs):
        self.conn = self.loop.run_until_complete(asyncio.ensure_future(self.async_connect(*args, **kwargs)))

    async def async_connect(self, *args, **kwargs):
        self.conn = await asyncpg.connect(*args, **kwargs)

    def load(self, oid):
        self.loop.run_until_complete(self.async_load(oid))
        return self

    async def async_load(self, ident=None):
        self.oid = self.oid if ident is None else ident
        f = await self.fetchrow("""
            SELECT
            ordinances.file_id as file_code,
            ordinances.municipality_id as municipality_code,
            municipalities.prefecture_id as prefecture_code
            FROM ordinances
            INNER JOIN municipalities ON municipalities.id = municipality_code
            WHERE ordinances.id = $1;
        """, self.oid)
        self.__dict__.update(f)
        return Root(self)

    def _get_law_name(self):
        self.conn.execute("SELECT name FROM ordinance WHERE id = $1", self.oid)

    def _get_law_num(self):
        self.conn.execute("SELECT num FROM ordinance WHERE id = $1", self.oid)

if __name__ == '__main__':
    import PostgresTables as ts

    ld = PostgresLaw()
    ld.connect(user="KazuyaFujioka", database="ordinance")
    asyncio.get_event_loop().run_until_complete(ld.conn.execute(ts.PREF_TABLE+ts.MUNI_TABLE+ts.ORD_TABLE))
