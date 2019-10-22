'''
Generate synthetic data that is "ideal"/realistic with 10 items
'''

import numpy as np
import _pickle as pkl

# The set of items in the dataset
items = ["Smartphone",      \
         "Phone Case",      \
         "Screen Guard",    \
         "Laptop",          \
         "Mouse",           \
         "Keyboard",        \
         "Smart TV",        \
         "Firestick",       \
         "Color Book",      \
         "Crayons"          ]

# The selling price of each item in the dataset
selling_price = {"Smartphone" : 10000,    \
        "Phone Case" : 500,     \
        "Screen Guard" : 200,   \
        "Laptop" : 40000,       \
        "Mouse" : 2000,          \
        "Keyboard" : 3000,       \
        "Smart TV" : 30000,     \
        "Firestick" : 5000,     \
        "Color Book" : 200,     \
        "Crayons" : 400         }

# The cost price of each item in the dataset
cost_price = {"Smartphone" : 4000,    \
        "Phone Case" : 100,     \
        "Screen Guard" : 50,   \
        "Laptop" : 10000,       \
        "Mouse" : 500,          \
        "Keyboard" : 750,       \
        "Smart TV" : 7500,     \
        "Firestick" : 1000,     \
        "Color Book" : 50,     \
        "Crayons" : 100         }

# The desired cooccurances in the dataset
probabilities_of_cooccurance = {"Smartphone" :      [1, 0.8, 0.6, 0.001, 0.05, 0.05, 0.01, 0.01, 0.01, 0.05],       \
                                "Phone Case" :      [0.1, 1, 0.95, 0.001, 0.005, 0.005, 0.001, 0.001, 0.03, 0.03],  \
                                "Screen Guard" :    [0.05, 0.9, 1, 0.001, 0.005, 0.005, 0.001, 0.001, 0.03, 0.03],  \
                                "Laptop" :          [0.001, 0.005, 0.005, 1, 0.9, 0.9, 0.001, 0.005, 0.01, 0.01],   \
                                "Mouse" :           [0.001, 0.01, 0.01, 0.001, 1, 0.9, 0, 0.001, 0.02, 0.02],       \
                                "Keyboard" :        [0.001, 0.01, 0.01, 0.001, 0.95, 1, 0, 0.001, 0.02, 0.02],      \
                                "Smart TV" :        [0.05, 0.1, 0.1, 0.01, 0.5, 0.5, 1, 0.95, 0.05, 0.05],          \
                                "Firestick" :       [0.01, 0.05, 0.05, 0.01, 0.3, 0.3, 0.1, 1, 0.02, 0.02],         \
                                "Color Book" :      [0.001, 0.01, 0.01, 0, 0.1, 0.05, 0, 0.001, 1, 0.95],           \
                                "Crayons" :         [0, 0.02, 0.02, 0, 0.05, 0.1, 0, 0, 0.5, 1]                     }

if __name__ == "__main__":
    data = []
    for i in range(len(items)):
        for _ in range(10000):
            invoice = []
            for j in range(len(items)):
                prob = np.random.uniform(0, 1)
                if prob <= probabilities_of_cooccurance[items[i]][j]:
                    invoice.append(1)
                else:
                    invoice.append(0)

            data.append(invoice)

    data = np.array(data)
    print(data.shape)
    cooccurance_matrix = np.matmul(np.transpose(data), data)
    user_vector = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    recommendation_vector = np.matmul(cooccurance_matrix, user_vector)
    print(recommendation_vector)

    final_data = {"items" : items, "selling_price" : selling_price, "cost_price" : cost_price, "cooccurance_matrix" : cooccurance_matrix}
    pkl.dump(final_data, open("./data.pkl", 'wb'))