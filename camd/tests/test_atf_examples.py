import unittest
import os
import tempfile
import shutil
import pandas as pd

from sklearn.neural_network import MLPRegressor
from camd.agent.agents import QBCStabilityAgent, GaussianProcessStabilityAgent, SVGProcessStabilityAgent, \
    BaggedGaussianProcessStabilityAgent, AgentStabilityAdaBoost
from camd.agent.base import RandomAgent
from camd.analysis import AnalyzeStability as AnalyzeStability
from camd.experiment import ATFSampler
from camd.loop import Loop
from camd.utils.data import cache_matrio_data, load_dataframe
from camd import CAMD_TEST_FILES


CAMD_LONG_TESTS = os.environ.get("CAMD_LONG_TESTS", False)
SKIP_MSG = "Long tests disabled, set CAMD_LONG_TESTS to run long tests"


@unittest.skipUnless(CAMD_LONG_TESTS, SKIP_MSG)
class AftLoopTestLong(unittest.TestCase):
    def setUp(self):
        self.pwd = os.getcwd()
        self.tempdir = tempfile.mkdtemp()
        os.chdir(self.tempdir)

    def tearDown(self):
        os.chdir(self.pwd)
        shutil.rmtree(self.tempdir)

    def test_random_agent_loop(self):

        df = load_dataframe("oqmd1.2_exp_based_entries_featurized_v2")
        n_seed = 5000
        n_query = 200
        agent = RandomAgent
        agent_params = {
            'hull_distance': 0.05,
            'n_query': n_query,
        }
        analyzer = AnalyzeStability
        analyzer_params = {'hull_distance': 0.05}
        experiment = ATFSampler
        experiment_params = {'params': {'dataframe': df}}
        candidate_data = df
        path = '.'

        new_loop = Loop(candidate_data, agent, experiment, analyzer,
                        agent_params=agent_params, analyzer_params=analyzer_params, experiment_params=experiment_params,
                        create_seed=n_seed)

        new_loop.initialize()
        self.assertFalse(new_loop.create_seed)

        for _ in range(6):
            new_loop.run()
            self.assertTrue(True)

    def test_qbc_agent_loop(self):
        pass


class AtfLoopTest(unittest.TestCase):
    def setUp(self):
        self.pwd = os.getcwd()
        self.tempdir = tempfile.mkdtemp()
        os.chdir(self.tempdir)

    def tearDown(self):
        os.chdir(self.pwd)
        shutil.rmtree(self.tempdir)

    def test_random_agent_loop(self):
        df = pd.read_csv(os.path.join(CAMD_TEST_FILES, 'test_df.csv'))
        n_seed = 200  # Starting sample size
        n_query = 10  # This many new candidates are "calculated with DFT" (i.e. requested from Oracle -- DFT)
        agent = RandomAgent
        agent_params = {'n_query': n_query}
        analyzer = AnalyzeStability
        analyzer_params = {'hull_distance': 0.05}
        experiment = ATFSampler
        experiment_params = {'dataframe': df}
        candidate_data = df
        new_loop = Loop(candidate_data, agent, experiment, analyzer,
                        agent_params=agent_params, analyzer_params=analyzer_params,
                        experiment_params=experiment_params,
                        create_seed=n_seed)

        new_loop.initialize()
        self.assertFalse(new_loop.create_seed)

        for _ in range(6):
            new_loop.run()
            self.assertTrue(True)

        # Testing the continuation
        new_loop = Loop(candidate_data, agent, experiment, analyzer,
                        agent_params=agent_params, analyzer_params=analyzer_params,
                        experiment_params=experiment_params,
                        create_seed=n_seed)
        self.assertTrue(new_loop.initialized)
        self.assertEqual(new_loop.iteration, 6)
        self.assertEqual(new_loop.loop_state, None)

        new_loop.run()
        self.assertTrue(True)
        self.assertEqual(new_loop.iteration, 7)

    def test_qbc_agent_loop(self):
        df = pd.read_csv(os.path.join(CAMD_TEST_FILES, 'test_df.csv'))
        df_sub = df[df['N_species'] <= 3]
        n_seed = 200  # Starting sample size
        n_query = 10  # This many new candidates are "calculated with DFT" (i.e. requested from Oracle -- DFT)
        agent = QBCStabilityAgent
        agent_params = {
            'ml_algorithm': MLPRegressor,
            'ml_algorithm_params': {'hidden_layer_sizes': (84, 50)},
            'n_query': n_query,
            'n_members': 10,  # Committee size
            'hull_distance': 0.05,  # Distance to hull to consider a finding as discovery (eV/atom)
            'alpha': 0.5  # Fraction to exploit (rest will be explored -- randomly picked)
        }
        analyzer = AnalyzeStability
        analyzer_params = {'hull_distance': 0.05}
        experiment = ATFSampler
        experiment_params = {'dataframe': df_sub}
        candidate_data = df_sub
        path = '.'

        new_loop = Loop(candidate_data, agent, experiment, analyzer,
                        agent_params=agent_params, analyzer_params=analyzer_params,
                        experiment_params=experiment_params,
                        create_seed=n_seed)
        new_loop.initialize()
        self.assertTrue(new_loop.initialized)

        new_loop.auto_loop(6)
        self.assertTrue(True)

    def test_simple_gp_loop(self):
        df = pd.read_csv(os.path.join(CAMD_TEST_FILES, 'test_df.csv'))
        df_sub = df[df['N_species'] <= 3]
        n_seed = 200  # Starting sample size
        n_query = 10  # This many new candidates are "calculated with DFT" (i.e. requested from Oracle -- DFT)
        agent = GaussianProcessStabilityAgent
        agent_params = {
            'n_query': n_query,
            'hull_distance': 0.05,  # Distance to hull to consider a finding as discovery (eV/atom)
            'alpha': 0.5  # Fraction of std to include in expected improvement
        }
        analyzer = AnalyzeStability
        analyzer_params = {'hull_distance': 0.05}
        experiment = ATFSampler
        experiment_params = {'dataframe': df_sub}
        candidate_data = df_sub
        path = '.'

        new_loop = Loop(candidate_data, agent, experiment, analyzer,
                        agent_params=agent_params, analyzer_params=analyzer_params,
                        experiment_params=experiment_params,
                        create_seed=n_seed)
        new_loop.initialize()
        self.assertTrue(new_loop.initialized)

        new_loop.auto_loop(6)
        self.assertTrue(True)

    def test_gp_bagging(self):
        df = pd.read_csv(os.path.join(CAMD_TEST_FILES, 'test_df.csv'))
        df_sub = df[df['N_species'] <= 3]
        n_seed = 200  # Starting sample size
        n_query = 10  # This many new candidates are "calculated with DFT" (i.e. requested from Oracle -- DFT)
        agent = BaggedGaussianProcessStabilityAgent
        agent_params = {
            'n_query': n_query,
            'hull_distance': 0.05,  # Distance to hull to consider a finding as discovery (eV/atom)
            'alpha': 0.5,  # Fraction of std to include in expected improvement
            'n_estimators': 2,
            'max_samples': 195
        }
        analyzer = AnalyzeStability
        analyzer_params = {'hull_distance': 0.05}
        experiment = ATFSampler
        experiment_params = {'dataframe': df_sub}
        candidate_data = df_sub
        path = '.'

        new_loop = Loop(candidate_data, agent, experiment, analyzer,
                        agent_params=agent_params, analyzer_params=analyzer_params,
                        experiment_params=experiment_params,
                        create_seed=n_seed)
        new_loop.initialize()
        self.assertTrue(new_loop.initialized)

        new_loop.auto_loop(6)
        self.assertTrue(True)

    def test_adaboost_loop(self):
        df = pd.read_csv(os.path.join(CAMD_TEST_FILES, 'test_df.csv'))
        df_sub = df[df['N_species'] <= 3]
        n_seed = 200  # Starting sample size
        n_query = 10  # This many new candidates are "calculated with DFT" (i.e. requested from Oracle -- DFT)
        agent = AgentStabilityAdaBoost
        agent_params = {
            'ml_algorithm': MLPRegressor,
            'ml_algorithm_params': {'hidden_layer_sizes': (84, 50)},
            'n_query': n_query,
            'hull_distance': 0.05,  # Distance to hull to consider a finding as discovery (eV/atom)
            'exploit_fraction': 1.0,  # Fraction to exploit (rest will be explored -- randomly picked)
            'alpha': 0.5,  # Fraction of std to include in expected improvement
            'n_estimators': 10
        }
        analyzer = AnalyzeStability
        analyzer_params = {'hull_distance': 0.05}
        experiment = ATFSampler
        experiment_params = {'dataframe': df_sub}
        candidate_data = df_sub
        path = '.'

        new_loop = Loop(candidate_data, agent, experiment, analyzer,
                        agent_params=agent_params, analyzer_params=analyzer_params,
                        experiment_params=experiment_params,
                        create_seed=n_seed)
        new_loop.initialize()
        self.assertTrue(new_loop.initialized)

        new_loop.auto_loop(6)
        self.assertTrue(True)

    def test_mp_loop(self):
        df = pd.read_csv(os.path.join(CAMD_TEST_FILES, 'test_df_analysis.csv'),)
                         # index_col="id")
        df['id'] = [int(mp_id.replace("mp-", "").replace('mvc-', ''))
                    for mp_id in df['id']]
        df.set_index("id")
        df['Composition'] = df['formula']

        # Just use the Ti-O-N chemsys
        seed_data = df.iloc[:38]
        candidate_data = df.iloc[38:209]
        n_query = 20  # This many new candidates are "calculated with DFT" (i.e. requested from Oracle -- DFT)
        agent = RandomAgent
        agent_params = {'n_query': n_query}
        analyzer = AnalyzeStability
        analyzer_params = {'hull_distance': 0.05}
        experiment = ATFSampler
        experiment_params = {'dataframe': df}
        # candidate_data = df
        new_loop = Loop(candidate_data, agent, experiment, analyzer,
                        agent_params=agent_params, analyzer_params=analyzer_params,
                        experiment_params=experiment_params, seed_data=seed_data)

        new_loop.initialize()
        self.assertFalse(new_loop.create_seed)

        for iteration in range(6):
            new_loop.run()
            self.assertTrue(
                os.path.isfile("hull_{}.png".format(iteration)))
            if iteration >= 1:
                self.assertTrue(
                    os.path.isfile("report.png"))

        # Testing the continuation
        new_loop = Loop(candidate_data, agent, experiment, analyzer,
                        agent_params=agent_params, analyzer_params=analyzer_params,
                        experiment_params=experiment_params)
        self.assertTrue(new_loop.initialized)
        self.assertEqual(new_loop.iteration, 6)
        self.assertEqual(new_loop.loop_state, None)

        new_loop.run()
        self.assertTrue(True)
        self.assertEqual(new_loop.iteration, 7)

@unittest.skipUnless(CAMD_LONG_TESTS, SKIP_MSG)
class AtfSVGPLoopTest(unittest.TestCase):
    def setUp(self):
        self.pwd = os.getcwd()
        self.tempdir = tempfile.mkdtemp()
        os.chdir(self.tempdir)

    def tearDown(self):
        os.chdir(self.pwd)
        shutil.rmtree(self.tempdir)

    def test_svgp_loop(self):
        df = pd.read_csv(os.path.join(CAMD_TEST_FILES, 'test_df.csv'))
        df_sub = df[df['N_species'] <= 3]
        n_seed = 200  # Starting sample size
        n_query = 10  # This many new candidates are "calculated with DFT" (i.e. requested from Oracle -- DFT)
        agent = SVGProcessStabilityAgent
        agent_params = {
            'n_query': n_query,
            'hull_distance': 0.05,  # Distance to hull to consider a finding as discovery (eV/atom)
            'alpha': 0.5,  # Fraction of std to include in expected improvement
            'M': 100  # number of inducing points for SVGP
        }
        analyzer = AnalyzeStability
        analyzer_params = {'hull_distance': 0.05}
        experiment = ATFSampler
        experiment_params = {'dataframe': df_sub}
        candidate_data = df_sub
        path = '.'

        new_loop = Loop(candidate_data, agent, experiment, analyzer,
                        agent_params=agent_params, analyzer_params=analyzer_params,
                        experiment_params=experiment_params,
                        create_seed=n_seed)
        new_loop.initialize()
        self.assertTrue(new_loop.initialized)

        new_loop.auto_loop(3)
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
