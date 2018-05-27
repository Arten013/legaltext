 # -*- coding: utf-8 -*-
import re
from pprint import pprint
import os
from glob import glob
import shutil
from sklearn.externals import joblib
from time import sleep
import datetime
from Dataset import Dataset
import psycopg2
from Parameters import ParameterSetBaseClass

class ModelWrapper(object):
    PARAMETERS_CLASS = None
    DATASET_CLASS = Dataset

    def __init__(self, *args, **kwargs):
        assert self.__class__.PARAMETERS_CLASS is not None, "Implementation error: You have to set PARAMETERS_CLASS"
        super().__init__(*args, **kwargs)
        self.datetime = datetime.datetime.now()
        self._id = None
        self.parameters = None
        self.dataset = None
        self._recoveried = False

    @property
    def id(self):
        if self._id is None:
            if self.parameters is not None and self.dataset is not None:
                self._load_from_metadata()
        return self._id

    @property
    def conn(self):
        assert self._conn is not None, "You must connect to db before using connection"
        return self._conn

    @property
    def type(self):
        return self.__class__.__name__

    @property
    def save_dir(self):
        if self.id is not None:
            return os.path.join(os.path.dirname(__file__), "models", self.type, "{id:04}-{name}".format(self.id, self.name))
        return None

    @property
    def recovery_dir(self):
        return os.path.join(os.path.dirname(self.save_dir), "recovery", self.name)

    @property
    def name(self):
        if "_name" not in self.__dict__ or self._name is None:
            self._name = self.datetime.strftime("%Y%m%d-%H%M%S")
        return self._name

    def connect(self, db, user):
        self._conn = psycopg2.connect("dbname={db} user={user}".format(db=db, user=user))

    def set_metadata(self, parameters, dataset, name=None):
        assert issubclass(parameters.__class__, ParameterSetBaseClass), "You must set parameters via child class of ParameterSetBaseClass"
        self.parameters = parameters

        assert issubclass(dataset.__class__, Dataset), "You must set dataset via child class of Dataset"
        assert len(dataset.ordinances) > 0 , "The dataset is empty"
        self.dataset = dataset

        self._name = None
        self._load_from_metadata()
        if self._name is None:
            self._name = name
        else:
            print("WARNING: While loading this model, model name has changed to the name which has already registered to the db as below.")
            print(name, "->", self.name)

    def _load_from_metadata(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                models.id,
                models.name
            FROM
                models
            INNER JOIN 
                {param_tbl} ON {param_tbl}.model_id = models.id
            WHERE
                {param_tbl}.id = %s
                AND models.dataset_id = %s
                AND model_type = %s
            """.format(param_tbl=self.parameters.table_name),
            (self.parameters.id, self.dataset.id, self.type)
            )
        ret = cursor.fetchone()
        if ret is not None:
            print("The model has already registered to the db.")
            print("Try to load model.")
            self._id, self._name = ret

    @classmethod
    def load_from_name(cls, name, db, user):
        model = cls()
        cursor = model.conn.cursor()
        # model探索
        cursor.execute(
            """
            SELECT 
                id, dataset_id
            FROM 
                models
            WHERE
                name = %s
                AND model_type = %s
            """,
            (name, model.type)
            )
        res = cursor.fetchone()
        if res is None:
            raise Exception('No "{model}"" model named "{name}"" found in the db.'.format(model=self.type, name=name))

        # modelを発見したならロード
        # model metadataをinstance変数に代入
        self._id, dataset_id = res
        self._name = name

        # paramsを取得
        self.parameters = PARAMETERS_CLASS.load_from_model_id(self.id, db, user)

        # datasetを取得
        self.dataset = DATASET_CLASS.load_from_id(dataset_id, db, user)
        try:
            self.load()
            return True
        except FileNotFoundError:
            # recordを削除
            print("There is no model files named", self.name)
            print("Delete invalid db record.")
            raise

    @classmethod
    def recovery(self):
        self._recoveried = True
        if os.path.exists(p):
            m = joblib.load(p)
            m.save()
            os.remove(p)
            exit()
        return

    def register(self):
        cursor = self.conn.cursor()
        if not self.dataset.is_locked():
            self.dataset.register()
        for i in range(5):
            try:
                cursor.execute(
                        """
                        INSERT INTO
                            models(name, model_type, dataset_id)
                        VALUES
                            (%s, %s, %s)
                        RETURNING
                            id;
                        """,
                        (self.name, self.type, self.dataset.id)
                    )
                self._id, = cursor.fetchone()
                self.conn.commit()
                assert self.id is not None, "save failure"
                if self.parameters.id is None:
                    self.parameters.register(self.id)
                return
            except:
                raise
                sleep(0.2)
        else:
            if self._recoveried:
                print("recovery failed. try again.")
                raise
            os.makedirs(self.recovery_dir, exist_ok=True)
            joblib.dump(self, os.path.join(self.recovery_dir, "model.m"))
            print("trained model has saved automatically to the path below")
            print(self.recovery_dir)
            print("use recovery.py to recover the model")
            raise

    def save(self, *args, **kwargs):
        print("Register the model to the db.")
        if self.id is not None:
            print("You cannot over write the model.")
            return False
        self.register()
        os.makedirs(self.save_dir)
        super().save(*args, **kwargs)
        return True

    def load(self, *args, **kwargs):
        super(*args, **kwargs)

    def is_similar(self):
        raise "This model is not intended to compare sentences"

    def __del__(self):
        if self._id is not None:
            for x in glob(os.path.join(self.save_dir, '.*')):
                if ".DS_Store" in x:
                    continue
                print("remove temporary directory:", x)
                shutil.rmtree(x)
            if os.access(self.save_dir, mode=os.F_OK):
                for x in glob(os.path.join(self.save_dir, '.*')):
                    print("remove temporary file:", x)
                    os.remove(x)
            try:
                os.rmdir(self.save_dir)
                print("remove empty box %s" % str(self.save_dir))
                if self.id is not None:
                    self.conn.cursor().execute("""
                        DELETE FROM models WHERE id = $1"
                        """, self.id
                        )
                print("delete record")
            except:
                pass


