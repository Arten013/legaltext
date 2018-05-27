import asyncio
import janus
import concurrent.futures
import psycopg2

class Dataset(object):
    def __init__(self, name, unit_type):
        self.name = name
        self.unit_type = unit_type
        self._id = None
        self._is_locked=None
        self.ordinances = list()
        self._conn = None

    @property
    def conn(self):
        assert self._conn is not None, "You must connect to db before using connection"
        return self._conn

    @property
    def table_name(self):
        return "dataset"

    @property
    def id(self):
        if self._id is None:
            self.reload()
        return self._id

    @property
    def loop(self):
        if "loop" not in self.__dict__:
            self.loop = asyncio.get_event_loop()

    @classmethod
    def load_from_id(cls, dataset_id, db, user):
        dataset = cls(None, None)
        dataset.connect(db=db, user=users)
        cursor = dataset.conn.cursor()
        res = cursor.execute("""
            SELECT
                name,
                unit_type,
                ordinance_id_list
            FROM
                datasets
            WHERE
                id = %s
            ;
            """,
            (dataset_id,)
            ).fetchone()
        assert res is not None, "No dataset has registered whose dataset_id is {}".format(model_id)
        dataset._id = dataset_id
        dataset.name, dataset.unit_type, ord_id_list = res
        for oid in ord_id_list:
            l = Law()
            l.oid = oid
            dataset.add_ordinance(l)

    @classmethod
    def load_from_name(cls, name, db, user):
        dataset = cls(name, "")
        dataset.connect(db=db, user=user)
        dataset.reload()
        if not dataset.is_locked():
            raise Exception("load failure")
        return dataset

    def reload(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT 
                id, ordinance_id_list
            FROM 
                datasets
            WHERE 
                name=%s
            ;
            """, (self.name ,)
            )
        tmp = cursor.fetchone()
        if tmp is None:
            self._is_locked = False
        else:
            self._is_locked = True
            self._id, ordinance_id_list = tmp
            for oid in ordinance_id_list()

    def is_locked(self):
        if self._is_locked is None:
            self.reload()
        return self._is_locked

    def lock(self):
        self._is_locked = True

    def connect(self, db=None, user=None):
        self.db = self.db if db is None else db
        self.user = self.user if user is None else user
        self._conn = psycopg2.connect("dbname={db} user={user}".format(db=self.db, user=self.user))

    def add_ordinances(self, *ordinances):
        assert not self.is_locked(), "You cannot add ordinances to locked dbs."
        for o in ordinances:
            self.ordinances.append(o)
        
    def register(self):
        assert self.id is None, "The dataset {} has already registered".format(self.name)
        ord_id_list = [o.identifier for o in self.ordinances]
        print(ord_id_list)
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO datasets(name, unit_type, ordinance_id_list) VALUES(%s, %s, %s)",
            (self.name, self.unit_type, ord_id_list)
            )
        self.conn.commit()
        self.lock()

    async def __aiter__(self):
        assert not self.is_locked(), "You cannot iterate ordinances from unlocked dbs."
        for o in self.ordinances:
            await o.async_connect(database=self.db, user=self.user)
            root = await o.async_load()
            if root is not None:
                yield root

    def __iter__(self):
        assert not self.is_locked(), "You cannot iterate ordinances from unlocked dbs."
        for o in self.ordinances:
            o.connect(database=self.db, user=self.user)
            root = o.load()
            if root is not None:
                yield root


