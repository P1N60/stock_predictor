from sklearn.neural_network import MLPRegressor
import numpy as np

# Custom wrapper to handle dynamic hidden_layer_sizes
class MLPWrapper:
    def __init__(self, hidden_layer_amount=999, neuron_amount=999, **kwargs):
        self.hidden_layer_amount = hidden_layer_amount
        self.neuron_amount = neuron_amount
        self.kwargs = kwargs
        self.iter_no_change = round(2+1000/(np.sqrt(self.neuron_amount*self.hidden_layer_amount)))
        
    def fit(self, X, y):
        # Create tuple of hidden layer sizes
        hidden_layers = tuple([self.neuron_amount] * self.hidden_layer_amount)
        print(f"Trying: {self.hidden_layer_amount} layers, {self.neuron_amount} neurons per layer, iter_no_change={self.iter_no_change}")
        print(f"Hidden layer sizes: {hidden_layers}")
        self.model = MLPRegressor(
            hidden_layer_sizes=hidden_layers,
            learning_rate="adaptive",
            early_stopping=True,
            verbose=False,
            n_iter_no_change=self.iter_no_change,
            **self.kwargs
        )
        result = self.model.fit(X, y)
        print(f"Training completed. Iterations: {self.model.n_iter_}, Final score: {self.model.score(X, y):.4f} \n {"=" * 65}")
        return result
    
    def predict(self, X):
        return self.model.predict(X)
    
    def score(self, X, y):
        return self.model.score(X, y)
    
    def get_params(self, deep=True):
        params = {'hidden_layer_amount': self.hidden_layer_amount, 
                'neuron_amount': self.neuron_amount}
        params.update(self.kwargs)
        return params
    
    def set_params(self, **params):
        for key, value in params.items():
            setattr(self, key, value)
        return self