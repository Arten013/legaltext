from ModelBase import ModelWrapper
from Parameters import ParameterBaseClass, ParameterSetBaseClass
import joblib
from Dataset import Dataset

class TestModel(object):
    def __init__(self, pint, pstr):
        self.pint, self.pstr = pint, pstr
        print("TestModel: init")

    def set_pbool(self, pbool):
        self.pbool = pbool

    def save(self):
        assert "trained" in self.__dict__, "error with train"
        assert isinstance(self.trained), "error with train"
        joblib.dump((self.pint, self.pstr, self.pbool), self.save_dir)
        print("TestModel: save model")

    def load(self):
        self.pint, self.pstr, self.pbool = joblib.load(self.save_dir)
        assert isinstance(self.pint, int), "error with loading pint"
        assert isinstance(self.pstr, str), "error with loading pstr"
        assert isinstance(self.pbool, bool), "error with loading pbool"
        print("TestModel: load model")

    def train(self):
        assert isinstance(self.pint, int), "error with pint"
        assert isinstance(self.pstr, str), "error with pstr"
        assert isinstance(self.pbool, bool), "error with pbool"
        for root in self.dataset:
            for ce in root.iter_descendants():
                print(ce)
        print("TestModel: train model")
        self.trained = self

class Pint(ParameterBaseClass):
    PYCLS = int

class Pstr(ParameterBaseClass):
    PYCLS = str

class Pbool(ParameterBaseClass):
    PYCLS = bool

class TestModelParams(ParameterSetBaseClass):
    REQUIRED = [Pint, Pstr]
    OPTIONAL = {Pbool: Pbool(True)}
    WRAPPED_MODEL = TestModel

class WrappedTestModel(ModelWrapper, TestModel):
    PARAMETERS_CLASS = TestModelParams

if __name__ == "__main__":
    from EtreeLaw import EtreeLaw
    import psycopg2
    db = "ordinance_test"
    user = "KazuyaFujioka"
    """
    conn = psycopg2.connect("dbname={db} user={user}".format(db=db, user=user))
    conn.cursor().execute(TestModelParams.sql_drop_table())
    conn.commit()
    with open("./Etype.sql") as f:
        conn.cursor().execute(f.read())
    with open("./Dataset.sql") as f:
        conn.cursor().execute(f.read())
    conn.commit()
    conn.close()
    """

    # parameter test
    params = TestModelParams()
    params.connect(db=db, user=user)
    params.set(
        Pint(5),
        Pstr("hogefuga"),
        Pbool(True)
        )

    # dataset test
    """
    dataset = Dataset("test_dataset", "Article")
    dataset.connect(db=db, user=user)
    laws = []
    for i in range(5):
        laws.append(EtreeLaw())
        laws[-1].set("/Users/KazuyaFujioka/Documents/all_data/23/230006/{0:04}.xml".format(i+1))
    dataset.add_ordinances(*laws)
    """
    dataset = Dataset.load_from_name("test_dataset", db, user)

    # modelwrapper test
    model = WrappedTestModel(**params.as_kwargs("pint", "pstr"))
    model.connect(db=db, user=user)
    model.set_pbool(**params.as_kwargs("pbool"))
    model.set_metadata(parameters=params, dataset=dataset, name="testmodel")
    model.train()
    model.save()






