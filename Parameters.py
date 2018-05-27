from decimal import Decimal
import psycopg2

class ParameterBaseClass(object):
    TDICT_PYCLS_PGTYPES = {
        list: "ANYARRAY",
        bool: "BOOL",
        bytes: "BYTEA",
        str: "TEXT",
        float: "FLOAT",
        int: "INTEGER",
        Decimal: "NUMERIC",
    }
    CONSTRAINTS = ""
    PYCLS = None

    def __init__(self, val):
        self.val = val

    def __str__(self):
        return "{type}({val})".format(type=self.name, val=str(self.val))

    @property
    def name(self):
        return self.__class__.__name__.lower()

    @property
    def pgtype(self):
        return self.__class__.TDICT_PYCLS_PGTYPES[self.__class__.PYCLS]

    @classmethod
    def to_definition(cls, *additional_constraints):
        d = "{param} {pgtype} {constraints}".format(
            param=cls(None).name,
            pgtype=cls(None).pgtype,
            constraints=" ".join([cls.CONSTRAINTS] + list(additional_constraints))
            )
        return d

class ParameterSetBaseClass(object):
    REQUIRED = list()
    OPTIONAL = dict()
    WRAPPED_MODEL = None

    def __init__(self, conn=None):
        assert self.__class__.WRAPPED_MODEL is not None, "You must define WRAPPED_MODEL"
        self.req = dict()
        self.opt = dict()
        self._conn = conn
        self._id = None

    @property
    def conn(self):
        assert self._conn is not None, "You must connect to db before using connection"
        return self._conn

    @property
    def table_name(self):
        return "{0}_pamareters".format(self.WRAPPED_MODEL.__name__.lower())

    @property
    def id(self):
        if self._id is None:
            cursor = self.conn.cursor()
            cursor.execute(*self.sql_select())
            tmp = cursor.fetchone()
            if tmp is not None:
                self.param_id = tmp[0]
        return self._id

    @classmethod
    def load_from_model_id(cls, model_id, db, user):
        params = cls()
        params.connect(db=db, user=users)
        cursor = params.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        res = cursor.execute("""
            SELECT
                *
            FROM
                {tbl}
            WHERE
                model_id = $1
            ;
            """.format(params.table_name),
            pid
            ).fetchone()
        assert res is not None, "No parameter has registered whose model_id is {}".format(model_id)
        params._id = param_id
        for k, v in params.items():
            if not k in ["id", "model_id"]:
                params.set(globals()[k.capitalize()](v))
        return params

    def as_kwargs(self, *names):
        return {k:self[k] for k in names}

    def connect(self, db, user):
        self._conn = psycopg2.connect("dbname={db} user={user}".format(db=db, user=user))
        self.init_table()

    def init_table(self):
        cursor = self.conn.cursor()
        cursor.execute(self.sql_create_table())
        self.conn.commit()

    def set(self, *params):
        for param in params:
            assert issubclass(param.__class__, ParameterBaseClass), "Invalid class for parameter: "+str(param.__class__)
            if param.__class__ in self.__class__.REQUIRED:
                self.req[param.name] = param
            elif param.__class__ in self.__class__.OPTIONAL:
                self.opt[param.name] = param
            else:
                raise Exception(str(param)+" is invalid parameter for the class")

    def register(self, model_id):
        cursor = self.conn.cursor()
        cursor.execute(*self.sql_insert(model_id))
        self.conn.commit()

    def __getitem__(self, key):
        if key in self.req:
            return self.req[key].val
        elif key in self.opt:
            return self.opt[key].val
        elif self.__class__.OPTIONAL[key]:
            return self.__class__.OPTIONAL[key].val
        raise KeyError(key)

    @classmethod
    def get_pnames(cls):
        return sorted(list(map(lambda c: c(None).name, cls.REQUIRED+list(cls.OPTIONAL.keys()))))

    @classmethod
    def sql_create_table(cls):
        req_defs = [c.to_definition("NOT NULL") for c in sorted(cls.REQUIRED, key=lambda x: x.__name__)]
        opt_defs = [d.to_definition("DEFAULT {}".format(d.val)) for n, d in sorted(cls.OPTIONAL.items(), key=lambda x: x[0])]
        defs = ",\n".join(req_defs+opt_defs)
        return """
        CREATE TABLE IF NOT EXISTS {tbl}(
            id SERIAL PRIMARY KEY,
            model_id INTEGER REFERENCES models(id) ON DELETE CASCADE,
            {defs},
            UNIQUE({pnames})
        );
        """.format(tbl=cls().table_name, defs=defs, pnames=", ".join(cls.get_pnames()))

    @classmethod
    def sql_drop_table(cls):
        return "DROP TABLE {};".format(cls().table_name)

    def sql_insert(self, model_id):
        assert len(self.req.keys()) == len(self.__class__.REQUIRED), "Shortage of required parameters: "+str(set(self.__class__.REQUIRED)-set(self.req.keys()))
        pnames = self.get_pnames()
        ret = ("""
        INSERT INTO {tbl}({pnames}, model_id)
        VALUES({vals}, %s)
        RETURNING id;
        """.format(
            tbl=self.table_name,
            pnames=", ".join(pnames),
            vals=", ".join(["%s"]*len(pnames))
        ), list(map(lambda x: self[x], pnames)))+[model_id]
        print(*ret)
        return ret

    def sql_select(self):
        assert len(self.req.keys()) == len(self.__class__.REQUIRED), "Shortage of required parameters: "+str(set(self.__class__.REQUIRED)-set(self.req.keys()))
        pnames = self.get_pnames()
        return """
        SELECT id
        FROM {tbl}
        WHERE {queries};
        """.format(
            tbl=self.table_name,
            queries="\nAND ".join(["{} = %s".format(pname) for pname in pnames])
        ), list(map(lambda x: self[x], pnames))