import numpy as np
from utils import r2_score, mean_squared_error, A_R2, NRMSE, transforming_predictorspace, standardicing_responce

class NeuralNetRegressor:

    """Multi-layer perceptron for regression.

    Parameters
    ------------
    n_hidden : array-like (default: 30)
        The integer in position i tells you how many nodes hidden layer i contains.
    epochs : int (default: 100)
        Number of passes over the training set.
    eta : float (default: 0.001)
        Learning rate.
    shuffle : bool (default: True)
        Shuffles training data every epoch if True to prevent circles.
    batch_size : int (default: 1)
        Number of training samples per minibatch used in the stochastic gradient descent.
        (One gradient update per minibatch)
    seed : int (default: None)
        Random seed for initalizing weights and shuffling.
    key : string (default "sigmoid")
        Choosing the activationfunction.
    alpha : float (default 0.0001)
        The steepnes of the activation function elu. UPDATE

    Attributes
    -----------
    eval_ : dict
      Dictionary collecting the cost, training accuracy,
      and validation accuracy for each epoch during training.

    W_h : array-like, shape = [n_features, n_hidden]
        Weights in the hidden layer after fitting.

    b_h : 1d-array, shape = [1, n_hidden]
        Bias in the hidden layer after fitting.

    w_out : 1d-array shape = [n_hidden, 1]
      Output weights after fitting.

    b_out : int
        Output bias after fitting.

    """
    def __init__(self, n_hidden = [30],  epochs=100, eta=0.001, shuffle=True,
                 batch_size=1, seed=None, alpha=0.0001, activation='sigmoid'):

        self.random = np.random.RandomState(seed)
        self.n_hidden = n_hidden
        #self.l2 = l2
        self.epochs = epochs
        self.eta = eta
        self.shuffle = shuffle
        self.batch_size = batch_size
        self.alpha = alpha
        self.activation = activation
        self.n_hidden_layers = len(self.n_hidden)

        self.W_h = None
        self.b_h = None
        self.W_out = None
        self.b_out = None

        # Averaged over epoch
        self.train_perfom = None
        self.test_perfom = None
        
        self.model_error = None

    def activate(self, Z, kind='elu', deriv=False):

        if kind == 'sigmoid':
            a = 1. / (1. + np.exp(-np.clip(Z, -250, 250)))
            if deriv:
                return a * (1. - a)
            #return 1 / (1 + np.exp(Z))
            return a
        elif kind == 'elu':
            if deriv:
                Z_deriv = np.ones((np.shape(Z)), dtype=float)
                Z_deriv[np.where(Z < 0)] = self.alpha * np.exp(np.clip(Z[np.where(Z < 0)], -250, 250))
                return Z_deriv
            else:
                Z_out = np.copy(Z)
                Z_out[np.where(Z < 0)] = self.alpha * (np.exp(np.clip(Z[np.where(Z < 0)], -250, 250)) - 1)
                return Z_out
        elif kind == "linear":
            if deriv:
                return 1
            else:
                return Z
        else:
            raise ValueError('Invalid activation function {}'.format(kind))

        return None

    def initialize_weights_and_bias(self, X_train):
        """ initalizing weight and biases in both hidden and output layer.

        X_train: array, shape = [n_samples, n_features]
            Input layer with original features.
        """
        n_samples, n_features = np.shape(X_train)
        n_output = 1 
        
        # This is the numeber of gridcells and we want to make one prediction pr cell. 
        # It this doesn't work calculate the number of griddcells.

        self.b_h =  [] #np.ones((self.n_hidden_layers, self.n_hidden[0]))
        self.W_h = []

        for i in range(len(self.n_hidden)):
            if (i == 0):
                self.W_h.append(self.random.normal(loc=0.0, scale=0.1, size=(n_features, self.n_hidden[0])))
                self.b_h.append(np.ones(self.n_hidden[0]))
            else:
                self.W_h.append(self.random.normal(loc=0.0, scale=0.1, size=(self.n_hidden[i-1], self.n_hidden[i])))
                self.b_h.append(np.ones(self.n_hidden[i]))       
            
        self.b_out = [1]
        self.W_out = self.random.normal(loc=0.0, scale=0.1, size=(self.n_hidden[-1], n_output))
        
        
    def _forwardprop(self, X):
        """Compute forward propagation step

        X : array, shape = [n_samples, n_features]
            Input layer with original features.
        """
        A_hidden = []
        Z_hidden = []
        
        #print("self.n_hidden_layers: " , self.n_hidden_layers)
        #print("self.W_h[i] ", np.shape(self.W_h[0]))
        for i in range(self.n_hidden_layers):
            if i == 0:
                z_temp =  np.dot(X, self.W_h[i]) + self.b_h[i]
                #print(z_temp)
            else:
                z_temp = np.dot(a_temp, self.W_h[i]) + self.b_h[i]
                #print(z_temp)
                
            Z_hidden.append(z_temp)
            a_temp = self.activate(z_temp, self.activation, deriv = False)
            #print(a_temp)
            A_hidden.append(a_temp)

        Z_out = np.dot(a_temp, self.W_out) + self.b_out
        # Linear activation in the output layer when you have a regression problem
        A_out = Z_out

        return Z_hidden, A_hidden, Z_out, A_out

    def _backprop(self, y_train, X_train, A_hidden, Z_hidden, A_out, Z_out, batch_idx):
        """ Backpropagation algorithmn for MLP with a arbitrary number of hidden nodes and layers.

        X_train : array, shape = [n_samples, n_features]
            Input layer with original features.
        y_train : array, shape = [n_samples]
            Target class labels or data we want to fit.
        Z_hidden : (array-like) shape = []
          Signal into the hidden layer.
        A_hidden : (array-like) shape = []
          The activated signal into the hidden layer.
        Z_out :
            Signal into the output layer.
        A_out :
            Activated signal function.
        batch_idx : int
            The index where you iterate from.
        """

        # This is the derivative assuming our costfunction is 0.5*two_norm(A_out - y)**2
        # This results in different backpropagation 
        
        error_out = A_out - y_train[batch_idx].reshape(len(y_train[batch_idx]), 1)
          
        # Since we are in the regression case with a linear ouput funct.
        act_derivative_out = 1

        delta_out = error_out*act_derivative_out

        grad_w_out = np.dot(A_hidden[-1].T, delta_out)
        grad_b_out = np.sum(delta_out, axis=0)

        # Updating the output weights 
        self.W_out = self.W_out - self.eta * grad_w_out
        self.b_out = self.b_out - self.eta * grad_b_out
     
        
        # Looping over all the hidden layers except one
        # If the layer only have one layer it doesn't go into this while loop         
        
        i = 0
        while (i < self.n_hidden_layers-1):
            # Index moving backward in the layers.
            #print("this should only be one loop")
            layer_ind = self.n_hidden_layers - 1 - i
            #print("layer_ind:  : ", layer_ind)
            act_derivative_h = self.activate(Z_hidden[layer_ind], self.activation, deriv=True)
            
            if (i == 0):
                error_prev = np.dot(delta_out, self.W_out.T) * act_derivative_h
            else:
                #print("np.shape(error_prev)", np.shape(error_prev))
                error_prev = np.dot(error_prev, self.W_h[layer_ind+1].T) * act_derivative_h
            
            grad_w_h = np.dot(A_hidden[layer_ind - 1].T, error_prev)
            grad_b_h = np.sum(error_prev, axis=0)
            
            self.W_h[layer_ind] = self.W_h[layer_ind] - self.eta * grad_w_h
            self.b_h[layer_ind] = self.b_h[layer_ind] - self.eta * grad_b_h
            i += 1
            
   
        act_derivative_h = self.activate(Z_hidden[0], self.activation, deriv=True)  
    
        # Case with one hidden layer doesn't enter the while loop.
        if( self.n_hidden_layers == 1):
            error_last = np.dot(delta_out, self.W_out.T) * act_derivative_h
        else:
            error_last = np.dot(error_prev, self.W_h[layer_ind].T) * act_derivative_h

        grad_w_h = np.dot(X_train[batch_idx].T, error_last)
        grad_b_h = np.sum(error_last, axis = 0)

        self.W_h[0] = self.W_h[0] - self.eta * grad_w_h
        self.b_h[0] = self.b_h[0] - self.eta * grad_b_h

        return None


    def predict(self, X):
        """Predicts outcome of regression or class labels depending
        on the type of network you have initalized.

        Parameters
        -----------
        X : array, shape = [n_samples, n_features]
            Input layer with original features.

        Returns:
        ----------
        y_pred : array, shape = [n_samples]
            Regression nn : predicts outcome of regression.
            Classification : predicts class labels.

        """

        Z_hidden, A_hidden, Z_out, A_out = self._forwardprop(X)
        return Z_out

    def _minibatch_sgd(self, X_train, y_train):
        """
        Performes the stochastic gradient descent with mini-batches for one epoch.

        X_train : array, shape = [n_samples, n_features]
            Input layer with original features.
        y_train : array, shape = [n_samples]
            Target class labels or data we want to fit.

        """
        n_samples, n_features = np.shape(X_train)

        indices = np.arange(n_samples)

        if self.shuffle:
            self.random.shuffle(indices)

        for idx in range(0, n_samples, self.batch_size):

            batch_idx = indices[idx:idx + self.batch_size]

            # Forwardpropagation.
            Z_hidden, A_hidden, Z_out, A_out = self._forwardprop(
                X_train[batch_idx, :]
            )

            # Backpropagation.
            self._backprop(
                y_train, X_train, A_hidden, Z_hidden, A_out, Z_out, batch_idx
            )

        return self

    
    def fit(self, X_train, y_train, X_test=None, y_test=None):
        """ Learn weights from training data.

        Parameters
        -----------
        X_train : array, shape = [n_samples, n_features]
            Input layer with original features.
        y_train : array, shape = [n_samples]
            Target class labels or data we want to fit.
        X_test : array, shape = [n_samples, n_features]
            Sample features for validation during training.
        y_test : array, shape = [n_samples]
            Sample labels/data for validation during training.

        Returns:
        ----------
        self

        """

        self.initialize_weights_and_bias(X_train)

        # for progress formatting
        epoch_strlen = len(str(self.epochs))
        self.eval_ = {'cost_train': [], 
                      'cost_test': [], 
                      'train_preform': [], 
                      'valid_preform': [],
                      'train_preform_r2': [], 
                      'valid_preform_r2': []}

        # iterate over training epochs
        for epoch in range(self.epochs):

            # Includes forward + backward prop.
            self._minibatch_sgd( X_train, y_train)

            # Evaluation after each epoch during training
            z_h, a_h, z_out, a_out = self._forwardprop(X_train)
            _, _, _, a_out_test = self._forwardprop(X_test)

            y_train_pred = self.predict(X_train)
            y_test_pred = self.predict(X_test)

            y_test = y_test.reshape((len(y_test),1))
            y_train = y_train.reshape((len(y_train),1))

            y_test = standardicing_responce(y_test)
            y_test_pred = standardicing_responce(y_test_pred)
            
            y_train = standardicing_responce(y_train)
            y_train_pred = standardicing_responce(y_train) 
            
            train_preform = mean_squared_error(y_train, y_train_pred) 
            valid_preform = mean_squared_error(y_test, y_test_pred)
            
            train_preform_r2 = r2_score(y_train, y_train_pred) 
            valid_preform_r2 = r2_score(y_test, y_test_pred)

            self.eval_['train_preform'].append(train_preform)
            self.eval_['valid_preform'].append(valid_preform)
            self.eval_['train_preform_r2'].append(train_preform_r2)
            self.eval_['valid_preform_r2'].append(valid_preform_r2)

        # Calculate the error in the output
        self.model_error = np.subtract(y_train, y_train_pred)
            
        return self
