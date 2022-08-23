from math import ceil, log
from typing import Dict, List
from privacy_module import PEMPrivacyModule
from evaluate_module import EvaluateModule
from utils import plot_single_line, sort_by_frequency, visualize_frequency
import numpy as np

np.random.seed(123499)

class FAServerPEM():
    def __init__(self, n: int, m: int, k: int, varepsilon: float, batch_size: int, round: int, clients: List = [], privacy_mechanism_type: List = "GRR", evaluate_type: str = "F1", sampling_rate: float = 1):
        """_summary_

        Args:
            n (int): client size
            m (int): binary-string length
            k (int): top-k heavy hitters
            varepsilon (float): privacy budget
            batch_size (int): number of groups
            round (int): running round
            evaluate_type: evaluate function to estimate performance (NDCG or F1)
        """
        self.n = n
        self.sampling_rate = sampling_rate
        self.m = m
        self.k = k
        self.varepsilon = varepsilon
        self.batch_size = batch_size
        self.round = round
        self.clients = clients
        self.evaluate_type = evaluate_type
        self.evaluate_module = EvaluateModule(self.k, self.evaluate_type)

        self.__available_data_distribution = ["poisson", "uniform"]
        self.__available_privacy_mechanism_type = ["GRR", "None", "OUE", "PreHashing","GRR_Weight"]

        self.__init_privacy_mechanism(privacy_mechanism_type)

        if not self.clients:
            self.__init_clients()
        self.C_truth = sort_by_frequency(self.clients, self.k)
        

    def __init_privacy_mechanism(self, privacy_mechanism_type: str):
        self.privacy_mechanism_type = privacy_mechanism_type if privacy_mechanism_type in self.__available_privacy_mechanism_type else "GRR"
        print(f"Privacy Mechanism: {self.privacy_mechanism_type}")

    def __init_clients(self):
        type = input(
            f"simulate client data with ___ distribution {self.__available_data_distribution}: ")
        if type not in self.__available_data_distribution:
            print("Invalid distribution type:: Default distribution will be 'poisson'")
            type = "poisson"
        self.client_distribution_type = type
        self.__simulate_client(type)()
        self.n = int(self.n*self.sampling_rate)

    def __simulate_client_poisson(self, mu=None, var=None):
        if mu is None and var is None:

            mu = float(input("mean:"))

        clients = np.random.poisson(mu, self.n)
        self.clients = clients

    def __simulate_client_uniform(self, low=None, high=None):
        if low is None and high is None:

            low = int(input("low:"))
            high = int(input("high:"))

        clients = np.random.randint(low, high, self.n)
        clients = np.absolute(clients.astype(int))
        self.clients = clients

    def __simulate_client(self, type: str):
        if type == "poisson":
            return self.__simulate_client_poisson
        elif type == "uniform":
            return self.__simulate_client_uniform
        else:
            raise ValueError(
                f"Invalid client distribution type! Available types: {self.__available_data_distribution}")

    def predict_heavy_hitters(self) -> Dict:
        """_summary_

        Args:
            n (int): client size
            m (int): binary-string length
            k (int): top-k heavy hitters
            varepsilon (float): privacy budget
            batch_size (int): number of groups
        Returns:
            Dict: top-k heavy hitters C_g and their frequencies.
        """
        s_0 = ceil(log(self.k, 2))
        C_i = {}
        for i in range(2**s_0):
            C_i[i] = 0
        group_size = self.n//self.batch_size
        for i in range(1, self.batch_size+1):
            s_i = s_0 + ceil(i*(self.m-s_0)/self.batch_size)
            delta_s = ceil(i*(self.m-s_0)/self.batch_size) - \
                ceil((i-1)*(self.m-s_0)/self.batch_size)
            D_i = {}
            for val in C_i.keys():
                for offset in range(2**delta_s):
                    D_i[(val << delta_s) + offset] = 0

            privacy_module = PEMPrivacyModule(self.varepsilon, D_i, type=self.privacy_mechanism_type)
            # mechanism = privacy_mechanism(
            #     self.varepsilon, D_i, self.privacy_mechanism_type)
            mechanism = privacy_module.privacy_mechanism()
            handle_response = privacy_module.handle_response() 
            clients_responses = []

            for client in self.clients[(i-1)*group_size: (i)*group_size]:
                prefix_client = client >> (self.m-s_i)
                response = mechanism(prefix_client)
                clients_responses.append(response)

            D_i = handle_response(clients_responses)

            D_i_sorted = sorted(D_i.items(), key=lambda x: x[-1], reverse=True)


            C_i = {}
            for indx in range(min(self.k, len(D_i_sorted))):
                v, count = D_i_sorted[indx]
                if count > 0:
                    C_i[v] = count
            # print(f"Group {i} generated: {C_i}")
        return C_i

    def server_run(self):
        evaluate_score = 0
        for rnd in range(self.round):
            np.random.shuffle(self.clients)
            
            C_i = self.predict_heavy_hitters()

            C_i = list(C_i.keys())
            print(f"Truth ordering: {self.C_truth}")
            print(f"Predicted ordering: {C_i}")

            evaluate_score += self.evaluate_module.evaluate(self.C_truth, C_i)
        evaluate_score /= self.round
        print(
            f"ROUND {rnd} :: varepsilon = {self.varepsilon}, {self.evaluate_type}= {evaluate_score:.2f}")
        return self.varepsilon, evaluate_score

    def server_run_plot_varepsilon(self, min_varepsilon, step_varepsilon, max_varepsilon):
        self.varepsilon = min_varepsilon
        varepsilon_list = []
        evaluate_score_list = []
        while self.varepsilon < max_varepsilon:
            varepsilon, evaluate_score = self.server_run()
            varepsilon_list.append(varepsilon)
            evaluate_score_list.append(evaluate_score)
            self.varepsilon += step_varepsilon

        plot_single_line(varepsilon_list, evaluate_score_list, "varepsilon",
                         f"{self.evaluate_type}", f"{self.evaluate_type} vs varepsilon", k=self.k)
        return varepsilon_list, evaluate_score_list


if __name__ == '__main__':
    n = 1000

    m = 16
    k = 9
    init_varepsilon = 0.2
    step_varepsilon = 0.3
    max_varepsilon = 12
    batch_size = 9

    sampling_rate = 1
    round = 20 

    privacy_mechanism_type = "GRR" # ["GRR", "None","OUE"]
    evaluate_module_type = "NDCG" # ["NDCG", "F1"]

    server = FAServerPEM(n, m, k, init_varepsilon, batch_size, round, privacy_mechanism_type = privacy_mechanism_type, evaluate_type=evaluate_module_type, \
        sampling_rate= sampling_rate)
    server.server_run_plot_varepsilon(
        init_varepsilon,  step_varepsilon, max_varepsilon)

    visualize_frequency(server.clients, server.C_truth, server.client_distribution_type)
    