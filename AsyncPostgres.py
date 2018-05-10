import asyncio
import asyncpg

async def run():
    conn = await asyncpg.connect(user='user', password='password',
                                 database='database', host='127.0.0.1')
    values = await conn.fetch('''SELECT * FROM mytable''')
    await conn.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(run())

class AsyncSqlite(object):
    def __init__(self, dbfile, loop=None):
        self.dbfile = dbfile
        self.conn = apsw.Connection(self.dbfile)
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self._closed = asyncio.Event(loop=self.loop)
        self.conn.setbusytimeout(1000)
        self._closed.set()
        self.exectracers = []
        self.rowtracers = []
        self.executor = concurrent.futures.ThreadPoolExecutor(MAX_THREADS)

    def set_exectracer(self, tracer):
        self.conn.setexectrace(tracer)

    def set_rowtracer(self, tracer):
        self.conn.setrowtrace(tracer)

    async def connect(self):
        if not self.is_closed:
            raise Exception("Reconnection Error. You have to close connection before connecting")
        self._closed.clear()
        await self.exec_in_transaction("PRAGMA foreign_keys = ON;")
        await self.exec_in_transaction("BEGIN;")

    def na_execute(self, *args, **kwargs):
        future = self.execute(*args, **kwargs)
        return MyApswCursor(future)

    async def execute(self, statement, bindings=()):
        if self.is_closed:
            await self.connect()
        await self.exec_in_transaction(statement, bindings)
        await self.close()

    async def exec_in_transaction(self, statement, bindings=()):
        return 

    async def close(self, rollback=False):
        if self.is_closed:
            raise Exception("Connection Error. You have to connect db before closing")
        if rollback:
            await self.exec_in_transaction("Rollback;")
        else:
            await self.exec_in_transaction("Commit;")
        self._closed.set()

    @property
    def is_closed(self):
        return self._closed.is_set()

    def __del__(self):
        if not self.is_closed:
            print("ERROR EXIT ROLLBACK")
            self.conn.cursor().execute("Rollback;")