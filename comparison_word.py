"""_summary_
This experiment used to compare different models.
Returns:
    _type_: _description_
"""
from server_FedFT import FedFTServer
from server import FAServerPEM
from server_WT import WTServer
from triehh import SimulateTrieHH
from Cipher import *
from utils import plot_all_in_one, load_clients, visualize_frequency




if __name__ == '__main__':
    n = 2000

    m = 8
    k = 8
    init_varepsilon = 0.2
    step_varepsilon = 0.5
    max_varepsilon = 9 
    iterations = 4

    round = 10

    # truth_top_k, clients = load_clients(filename="./dataset/triehh_clients.txt", k=k)
    truth_top_k =[]
    clients = []

    privacy_mechanism_type = "GRR_X" # ["GRR", "None","OUE"]
    evaluate_module_type = "NDCG" # ["NDCG", "F1"]

    # ----Weight Tree & Client Size fitting---- # 
    server = FedFTServer(n, m, k, init_varepsilon, iterations, round, clients=clients, C_truth=truth_top_k,
        privacy_mechanism_type = privacy_mechanism_type, evaluate_type=evaluate_module_type
        )

    xc, yc = server.server_run_plot_varepsilon(
        init_varepsilon,  step_varepsilon, max_varepsilon)
    # server.server_run()
   
   # ----Weight Tree---- # 
    server = WTServer(n, m, k, init_varepsilon, iterations, round,clients=clients, C_truth=truth_top_k, 
    privacy_mechanism_type = privacy_mechanism_type, evaluate_type=evaluate_module_type
        )

    # server.server_run()
    xn, yn = server.server_run_plot_varepsilon(
        init_varepsilon,  step_varepsilon, max_varepsilon)
    
    # ----Standard Tree---- #

    privacy_mechanism_type = "GRR" # ["GRR", "None","OUE"]
    server = FAServerPEM(n, m, k, init_varepsilon, iterations, round, clients=clients, C_truth=truth_top_k, \
        privacy_mechanism_type = privacy_mechanism_type, evaluate_type=evaluate_module_type)
 
    x, y = server.server_run_plot_varepsilon(
    init_varepsilon,  step_varepsilon, max_varepsilon)

    # ----TrieHH Tree---- #
    delta = 1/(n**2)
    # evaluate_module_type = "NDCG" # ["NDCG", "F1"]

    server = SimulateTrieHH(n, m, k, init_varepsilon, iterations, round, clients=clients, C_truth=truth_top_k,  
            delta=delta, evaluate_type=evaluate_module_type)
    # server.server_run()
    x_triehh, y_triehh = server.server_run_plot_varepsilon(
        init_varepsilon,  step_varepsilon, max_varepsilon)


    ## Visualize Comparison ##
    xs = [xc, xn, x, x_triehh]
    ys = [yc, yn, y, y_triehh]

    plot_all_in_one(xs, ys, "privacy budget", evaluate_module_type, "Compare with using incremental client_size", ["FedFT", "Weight Tree", "Standard Tree", "TrieHH"] )
    
