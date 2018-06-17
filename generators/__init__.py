class BaseGen(object):
    id = None # Unique identifier used to register generator
    name = None # Name of generator

    @staticmethod
    def genflag(challenge): # Override this method
        pass

"""
Global dictionary used to hold all generators.
Insert into this dictionary to register your generator
"""
GENERATOR_CLASSES = {}
