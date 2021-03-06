# Copyright Toyota Research Institute 2019

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold, cross_val_score
from camd import tqdm

import abc


class HypothesisAgent(metaclass=abc.ABCMeta):
    def __init__(self):
        pass

    @abc.abstractmethod
    def get_hypotheses(self, candidate_data):
        """

        Returns:
            subset of candidate data which represent some
            choice e. g. for the next set of experiments

        """


class QBC:
    """
    Helper class for Uncertainty quantification using
    non-supporting regressors with Query-By-Committee
    """
    def __init__(self, n_members, training_fraction, ml_algorithm=None,
                 ml_algorithm_params=None, test_full_model=True):
        """
        n_members (int): Number of committee members (i.e. models to train)
        training_fraction (float): fraction of data to use in training committee members
        ml_algorithm (sklearn.RegressorMixin): sklearn-style regressor for
            regression algorithm
        ml_algorithm_params (dict): parameters to pass to the algorithm
        """
        self.n_members = n_members
        self.training_fraction = training_fraction
        self.ml_algorithm = ml_algorithm if ml_algorithm else LinearRegression
        self.ml_algorithm_params = ml_algorithm_params if ml_algorithm_params else {}
        self.committee_models = []
        self.trained = False
        self.test_full_model = test_full_model
        self.cv_score = np.nan
        self._X = None
        self._y = None

    def fit(self, X, y):
        self._X, self._y = X, y

        split_X = []
        split_y = []

        for i in range(self.n_members):
            a = np.arange(len(X))
            np.random.shuffle(a)
            indices = a[:int(self.training_fraction * len(X))]
            split_X.append(X.iloc[indices])
            split_y.append(y.iloc[indices])

        self.committee_models = []
        for i in tqdm(list(range(self.n_members))):
            scaler = StandardScaler()
            X = scaler.fit_transform(split_X[i])
            y = split_y[i]
            model = self.ml_algorithm(**self.ml_algorithm_params)
            model.fit(X, y)
            self.committee_models.append([scaler, model])  # Note we're saving the scaler to use in predictions

        self.trained = True

        if self.test_full_model:
            # Get a CV score for an overall model with present dataset
            overall_model = self.ml_algorithm(**self.ml_algorithm_params)
            overall_scaler = StandardScaler()
            _X = overall_scaler.fit_transform(self._X, self._y)
            overall_model.fit(_X, self._y)
            cv_score = cross_val_score(overall_model, _X, self._y,
                                       cv=KFold(5, shuffle=True), scoring='neg_mean_absolute_error')
            self.cv_score = np.mean(cv_score) * -1

    def predict(self, X):
        # Apply the committee of models to candidate space
        committee_predictions = []
        for i in tqdm(list(range(self.n_members))):
            scaler = self.committee_models[i][0]
            model = self.committee_models[i][1]
            _X = scaler.transform(X)
            committee_predictions.append(model.predict(_X))
        stds = np.std(np.array(committee_predictions), axis=0)
        means = np.mean(np.array(committee_predictions), axis=0)
        return means, stds


class RandomAgent(HypothesisAgent):
    """
    Baseline agent: Randomly picks from candidate dataset
    """
    def __init__(self, candidate_data=None, seed_data=None, n_query=1):

        self.candidate_data = candidate_data
        self.seed_data = seed_data
        self.n_query = n_query
        self.cv_score = np.nan
        super(RandomAgent, self).__init__()

    def get_hypotheses(self, candidate_data, seed_data=None):
        """

        Args:
            candidate_data (DataFrame): candidate data
            seed_data (DataFrame): seed data

        Returns:
            (List) of indices

        """
        return candidate_data.sample(self.n_query).index.tolist()
