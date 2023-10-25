class InverseTranformer:
    def __init__(self, transformer):
        self.transformer = transformer

    
    

class Transformer:
    def __init__(self, function):
        self.function = function

    def __call__(self, X):
        return self.function(X)
    def inverse(self):
        return InverseTranformer(self)
    
    