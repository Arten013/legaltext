 # -*- coding: utf-8 -*-
import re
from pprint import pprint
from .sql.sql_deco import *
import os
from pathlib import Path
from abc import ABCMeta, abstractmethod
from .dataset import Dataset
from glob import glob
import shutil
from sklearn.externals import joblib
from time import sleep
from Decimal import Decimal
#from traceback import exc

@db_deco
def reg_params(table, timestamp, bindings_dict):
    bnames, bvals, i = ["timestamp"], [timestamp], 1
    for k, v in bindings_dict:
        bnames.append(k)
        bvals.append(v)
        i += 1
    cursor.execute("INSERT INTO {0}({1}) VALUES({2});".format(table,", ".join(bnames), ", ".join(["?"]*i)), bindings)


class ParameterBaseClass(object):
    PYCLS_PGTYPES = {
        list: "ANYARRAY",
        bool: "BOOL",
        bytes: "BYTEA",
        str: "TEXT",
        float: "FLOAT",
        int: "INTEGER",
        Decimal: "NUMERIC",
    }

    def __init__(self, val):
        self.val = val
        self._pgtype = pgtype

    @property
    def pgtype(self):
        if self._pgtype is None:
            self._pgtype = PYCLS_PGTYPES.get(self.pycls, "TEXT")
        return self._pgtype

    def to_definition(self):
        return "{param} {ptype} {constraints}".format(
            param=self.__class__.__name__,
            ptype=self.pgtype,
            constraints=self.__class__.constraints
            )
class 


class ModelWrapperBase(metaclass=ABCMeta):
    SAVE_DIR_BASE = os.path.join(os.path.dirname(__file__), "..", "body")
    DEFAULT_NAME_BASE = "model{0}"
    MODEL_TABLE_STATEMENT = ""
    PARAMS_TABLE_STATEMENT = ""
    PARAMATERS_TABLE_BASE = 
    PARAMETERS_DEFINITION = """
    
    """

    def _get_parameter_statements(params=None):
        params = """
        CREATE TABLE {model_type}_parameters(
        id SERIAL PRIMARY KEY,
        {params_definition}
        UNIQUE({params})
        );
        """.(
            model_type=self.__class__.__name__,
            params_definition=
            )

    def __init__(self, body, dataset=None, name=None, **params):
        self.init_table()
        self.recovery()
        if name is not None and self.load_from_name(name):
            return
        elif dataset is not None:
            self.register_model(body, dataset, name, **params)
        self._recoveried=False

    def init_table(self):
        # model/paramsテーブル初期化
        execute(self.PARAMS_TABLE_STATEMENT)
        execute(self.MODEL_TABLE_STATEMENT)

        # model typeの取得
        self.type, _ = parse_create_table(self.MODEL_TABLE_STATEMENT)
        print("Model Type:", self.type)

    def load_from_name(self, name):
        res = execute("SELECT id, name, dataset_id, param_id FROM {0} where name = ?;".format(self.type), (name,)).fetchone()
        if res is not None:
            self.model_id, self.name, self.dataset_id, self.param_id = res
            set_fetchdict(True)
            self.params = execute("SELECT * FROM {0}_params WHERE id = ?".format(self.type), (self.param_id,)).fetchone()
            dataset_params = execute("SELECT root_id, root_type, unit_type FROM dataset WHERE id = ?", (self.dataset_id,)).fetchone()
            set_fetchdict(False)
            self.dataset = Dataset(**dataset_params)
            self.save_path = os.path.join(self.SAVE_DIR_BASE, self.type, "{0:04}-{1}".format(self.model_id, str(self.name))) 
            try:
                self.load()
                return True
            except FileNotFoundError:
                print("There is no model files named", self.name)
                print("Delete invalid db record.")
                execute("DELETE FROM {0} where name = ?;".format(self.type), (name,))
                raise
        return False

    def register_model(self, body, dataset, name=None, **params):
        # paramsの登録
        _, columns = parse_create_table(self.PARAMS_TABLE_STATEMENT)
        self.params = get_default_params(columns)
        for k in columns.keys():
            if k in params:
                self.params[k] = params[k]
        res = execute("SELECT id FROM {0}_params WHERE {1};".format(self.type, " AND ".join(["{0} = :{0}".format(k) for k in self.params.keys()])), self.params).fetchone()
        if res is None:
            insert_dict(self.type+"_params", self.params)
            self.param_id, = execute("SELECT id FROM {0}_params WHERE {1};".format(self.type, " AND ".join(["{0} = :{0}".format(k) for k in self.params.keys()])), self.params).fetchone()
        else:
            self.param_id = res[0]
        print("Model Params:")
        pprint(self.params)

        # modelの登録
        self.body = body
        self.dataset = dataset
        self.dataset_id = dataset.dataset_id
        self.name = name
        res = execute("SELECT id, name FROM {0} WHERE dataset_id = ? AND param_id = ?;".format(self.type), (self.dataset_id, self.param_id)).fetchone()
        if res is None:
            self.model_id = None
            self.save_path = None
        else:
            self.model_id, self.name = res
            self.save_path = os.path.join(self.SAVE_DIR_BASE, self.type, "{0:04}-{1}".format(self.model_id, str(self.name))) 
            if os.access(self.save_path, mode=os.F_OK):
                print("The model {0} has already existed.".format(self.name))
                self.load()
        print("model initialization finished")

    def save_error(self):
        if self._recoveried:
            print("recovery failed. try again.")
            raise
        self.save_path = None
        self.model_id = None
        p = os.path.join(self.SAVE_DIR_BASE, self.type, "recovery_file")
        os.makedirs(p, exist_ok=True)
        joblib.dump(self, os.path.join(p, "model.m"))
        print("trained model has saved automatically to the path below")
        print(p)
        print("use recovery.py to recover the model")
        raise

    def recovery(self):
        p = os.path.join(self.SAVE_DIR_BASE, self.type, "recovery_file", "model.m")
        if os.path.exists(p):
            m = joblib.load(p)
            m.save()
            os.remove(p)
            exit()
        return

    @abstractmethod
    def save(self):
        print("Register the model to the db.")
        if self.model_id is not None:
            print("You cannot over write the model.")
            return False
        for i in range(5):
            try:
                self.model_id, = execute("INSERT INTO {0}(dataset_id, param_id, name) VALUES(?, ?, ?); SELECT id FROM {0} WHERE ROWID = last_insert_rowid();".format(self.type), (self.dataset_id, self.param_id, "")).fetchone()
                break
            except:
                sleep(0.1)
                pass
        else:
            self.save_error()

        if self.name is None:
            self.name = DEFAULT_NAME_BASE.format(self.model_id)
            for i in range(1000):
                try:
                    execute("UPDATE {0} SET name = ? WHERE id = ?".format(self.type), (self.name, self.model_id))
                    break
                except:
                    self.name = DEFAULT_NAME_BASE.format(self.model_id)+"({0})".format(i)
            else:
                print("model name duplication error.")
                self.save_error()
        else:
            name_base = self.name
            for i in range(1000):
                print(self.name)
                try:
                    execute("UPDATE {0} SET name = ? WHERE id = ?".format(self.type), (self.name, self.model_id))
                    break
                except:
                    self.name = name_base+"({0})".format(i)
            else:
                print("model name duplication error.")
                print(t)
                self.save_error()
        self.save_path = os.path.join(self.SAVE_DIR_BASE, self.type, "{0:04}-{1}".format(self.model_id, str(self.name)))
        print(self.save_path)
        os.makedirs(self.save_path)
        return True

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def train(self):
        pass

    @abstractmethod
    def test(self):
        pass

    def is_similar(self):
        raise "This model is not intended to compare sentences"

    def __del__(self):
        for x in glob(os.path.join(self.SAVE_DIR_BASE, self.type, '.*')):
            if ".DS_Store" in x:
                continue
            print("remove temporary directory:", x)
            shutil.rmtree(x)
        if self.save_path is not None:
            if os.access(self.save_path, mode=os.F_OK):
                for x in glob(os.path.join(self.save_path, '.*')):
                    print("remove temporary file:", x)
                    os.remove(x)
            try:
                os.rmdir(self.save_path)
                print("remove empty box %s" % str(self.save_path))
                execute("DELETE FROM {0} WHERE id = ?".format(self.type), self.model_id)
                print("delete record")
            except:
                pass

    def __getattr__(self, name):
        if name is not "body" and self.body is not None:
            return getattr(self.body, name)

if __name__ == "__main__":
    set_db_path("/Users/KazuyaFujioka/Documents/fd2v/dbfile/OrdinanceDB.db")
    import TableSchema as ts
    from gensim.models import Doc2Vec
    from dataset import Dataset
    from time import time
    import datetime
    from contextlib import contextmanager
    from timeit import default_timer
    from gensim.models.doc2vec import TaggedDocument

    set_tracer(False)
    
    class MyDoc2Vec(ModelWrapperBase):
        MODEL_TABLE_STATEMENT = ts.DOC2VEC_TABLE
        PARAMS_TABLE_STATEMENT =  ts.DOC2VEC_PARAMS_TABLE
        def __init__(self, dataset=None, name=None, **params):
            super().__init__(Doc2Vec(**params), dataset, name, **params)

        def test(self):
            sample_tag = self.body.docvecs.index_to_doctag(0)
            print(0, self.dataset.search_data_name(sample_tag))
            for rank, (i, sim) in enumerate(self.body.docvecs.most_similar(sample_tag)):
                print(rank, i, self.dataset.search_data_name(int(i)), sim)

        def save(self):
            super().save()
            self.body.save(os.path.join(self.save_path, "model"))
            print('save model:', os.path.join(self.save_path, "model"))

        def load(self):
            self.body = gensim.models.Doc2Vec.load(os.path.join(self.save_path, "model"))
            print('load model:', os.path.join(self.save_path, "model"))

        def train(self):
            @contextmanager
            def elapsed_timer():
                start = default_timer()
                elapser = lambda: default_timer() - start
                yield lambda: elapser()
                end = default_timer()
                elapser = lambda: end-start

            def iter_dataset():
                for i, s in self.dataset.iter_dataset():
                    #print(i, s[1:20])
                    yield TaggedDocument(words=s.split(" "), tags=[str(i)])
                raise StopIteration

            #モデル生成
            print("Build vocab")
            self.body.build_vocab(iter_dataset())
            print("docvec shape: ", self.body.docvecs.vectors_docs.shape)
            print("Build vocab done")

            alpha, min_alpha, passes = (self.params["alpha"], self.params["min_alpha"], self.params["epochs"])
            alpha_delta = (alpha - min_alpha) / passes

            print("START %s" % datetime.datetime.now())

            for epoch in range(self.params["epochs"]):
                t = time()
                # Train
                duration = 'na'
                self.body.alpha, self.body.min_alpha = alpha, alpha
                with elapsed_timer() as elapsed:
                    self.body.train(iter_dataset(), total_examples=model.corpus_count, epochs=self.params["epochs"])
                    duration = '%.1f' % elapsed()
                print('Completed pass %i at alpha %f' % (epoch + 1, alpha))
                print("time: {0}sec".format(time() - t))
                alpha -= alpha_delta
            print("END %s" % str(datetime.datetime.now()))



