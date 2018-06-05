from generators import GENERATOR_CLASSES
import random

class ExampleGenerator(BaseGen):
    id = "random"
    name = "random"

    @staticmethod
    def genflag(challenge):
        ran = random.randint(1,101)
        challenge.description = "Your flag is " + ran "."
        challenge.flag = str(ran)

GENERATOR_CLASSES['example'] = ExampleGenerator
