import numpy as np
import pandas as pd
import random
import pickle
import math

class Agent:
    def __init__(self, product_list, cost_price, selling_price, max_initial_discount_rate = 0.1, min_profit_margin = 0.3, num_rounds = 0.6):
        self.first_offer_value = -1
        self.product_list = product_list
        self.cost_price = cost_price
        self.selling_price = selling_price
        self.buyer_utility_list = []
        self.prev_agent_offers_list = []
        self.prev_agent_offers_utility_list = []
        self.rounds = num_rounds
        self.time = 0
        self.alpha = 0.4
        self.max_initial_discount_rate = max_initial_discount_rate
        self.min_agent_utility = 1
        self.min_profit_margin = min_profit_margin

    def opponentModel(self, proposed_offer, recommender):

        '''
        The Opponent Model in the BOA System

        Parameters:
            proposed_offer  - proposed offer by the buyer
            recommender     - the recommendation system used by the agent

        Returns:
            buyer_utility   - the buyer utility of proposed_offer
        '''

        # the index of the product the buyer wishes to buy
        product_idx = proposed_offer["Bundle"][-1]

        total_offered_price = proposed_offer["Cost"]
        total_selling_price = 0
        for i in proposed_offer["Bundle"]:
            total_selling_price += self.selling_price[self.product_list[i]]

        offer_value = (total_selling_price - total_offered_price) / total_selling_price
        if self.first_offer_value == -1:
            self.first_offer_value = offer_value

        current_bid_utility = offer_value / self.first_offer_value
        prior_utility = 0
        for i in proposed_offer["Bundle"][:-1]:
            prior_utility += recommender.cooccurance_matrix[product_idx][i] / recommender.cooccurance_matrix[product_idx][product_idx]

        prior_utility /= (len(proposed_offer["Bundle"]) - 1)
        lr = self.time**(-2.2)
        buyer_utility = (1 - lr) * current_bid_utility + lr * prior_utility

        return buyer_utility

    def utility(self, proposed_offer, recommender):
        '''
        Parameters:
            proposed_offer  - proposed offer by the buyer
            recommender     - the recommendation system used by the agent

        Returns:
            agent utility for the proposed offer
        '''

        # the index of the product the buyer wishes to buy
        product_idx = proposed_offer["Bundle"][-1]

        total_offered_price = proposed_offer["Cost"]
        total_selling_price = 0
        for i in proposed_offer["Bundle"]:
            total_selling_price += self.selling_price[self.product_list[i]]

        total_cost_price = 0
        for i in proposed_offer["Bundle"]:
            total_cost_price += self.cost_price[self.product_list[i]]

        profit = total_offered_price - total_cost_price
        max_profit = total_selling_price - total_cost_price
        agent_utility = profit / max_profit

        initial_profit = self.selling_price[self.product_list[product_idx]] - self.cost_price[self.product_list[product_idx]]
        self.min_agent_utility = (initial_profit + self.min_profit_margin*(max_profit - initial_profit)) / max_profit
        return agent_utility

    def TKI(self, buyer_utility, agent_utility):

        '''
        Thomas-Kilmann Conflict Mode Instrument used by the agent to measure the buyer's cooperativeness and assertiveness

        Parameters:
            buyer_utility   - buyer utility for the current round
            agent_utility   - agent utility for the current round

        Returns:
            target_utility  - the target utility of the offer that the agent should propose
        '''

        decay_factor = 1.3
        if len(self.buyer_utility_list) == 0:
            target_utility = self.min_agent_utility + (1-self.min_agent_utility) * (1 - decay_factor * buyer_utility * min(self.rounds + self.time * 0.1, 1) ** (1 / self.alpha))
            self.time += 1
            self.buyer_utility_list.append(buyer_utility)
            return target_utility
        else:
            mean_buyer_utility = np.mean(self.buyer_utility_list)
            var_buyer_utility = np.var(self.buyer_utility_list)
            current_var_buyer_utility = (buyer_utility - mean_buyer_utility) ** 2
            cooperativeness = ""
            assertiveness = ""
            if buyer_utility > mean_buyer_utility:
                cooperativeness = "uncooperative"
            elif buyer_utility == mean_buyer_utility:
                cooperativeness = "neutral"
            else:
                cooperativeness = "cooperative"

            if current_var_buyer_utility > var_buyer_utility:
                assertiveness = "passive"
            elif current_var_buyer_utility == var_buyer_utility:
                assertiveness = "neutral"
            else:
                assertiveness = "assertive"

            if (cooperativeness == "cooperative" and assertiveness == "passive"):
                if self.alpha < 1:
                    self.alpha += 0.15

            elif (cooperativeness == "neutral" and assertiveness == "neutral"):
                self.alpha -= 0.05
            else:
                if self.alpha > 0.3:
                    self.alpha -= 0.25

            target_utility = self.min_agent_utility + (1-self.min_agent_utility) * (1 - decay_factor * buyer_utility * min(self.rounds + self.time * 0.08, 1) ** (1 / self.alpha))

            self.time += 1
            self.buyer_utility_list.append(buyer_utility)
            return target_utility

    def getBidSpace(self, proposed_offer, target_utility, recommender, prev_offer):
        '''
        Provides a list of all reasonable bids that can be offered based on the
        target utility function offered by TKI

        Parameters:
            proposed_offer  - offer proposed by buyer
            target_utility  - the target utility of the offer that the agent should propose
            recommender     - the recommendation system used by the agent
            prev_offer      - previous offer made by the agent

        Returns:
            reasonable_bid_space - list of reasonable bids
        '''

        max_cost = int(prev_offer["Cost"])
        if not np.array_equal(sorted(prev_offer["Bundle"]), sorted(proposed_offer["Bundle"])):
            max_cost = int(self.getInitialOffer(proposed_offer["Bundle"], recommender)["Cost"])

        offered_price = proposed_offer["Cost"]
        # offered_price - (max_cost - offered_price)
        start_offer_price = max(0, 2*offered_price - max_cost)
        bid_space = []
        for price in range(start_offer_price, max_cost+1):
            bid_space.append({"Bundle" : proposed_offer["Bundle"], "Cost" : price})

        reasonable_bid_space = []
        for bid in bid_space:
            agent_utility = self.utility(proposed_offer, recommender)
            if abs(agent_utility - target_utility) <= 0.05:
                reasonable_bid_space.append(bid)

        return bid_space

    def acceptanceModel(self, bid_space, proposed_offer, target_utility, recommender, agent_utility):
        prev_offer_utility = self.prev_agent_offers_utility_list[-1]
        new_offer = {}
        prev_mean_utility = np.mean(self.prev_agent_offers_utility_list)
        bid_space_utility_list = [self.utility(offer, recommender) for offer in bid_space]

        if prev_offer_utility <= agent_utility:
            new_offer["Bundle"] = proposed_offer["Bundle"]
            new_offer["Cost"] = proposed_offer["Cost"]
            new_offer["Accepted"] = True

        elif prev_mean_utility <= agent_utility:
            new_offer["Bundle"] = proposed_offer["Bundle"]
            new_offer["Cost"] = proposed_offer["Cost"]
            new_offer["Accepted"] = True

        elif target_utility <= agent_utility:
            new_offer["Bundle"] = proposed_offer["Bundle"]
            new_offer["Cost"] = proposed_offer["Cost"]
            new_offer["Accepted"] = True

        else:
            min_difference_utility = math.inf
            for idx in range(len(bid_space_utility_list)):
                if min_difference_utility > abs(target_utility - bid_space_utility_list[idx]):
                    new_offer["Bundle"] = bid_space[idx]["Bundle"]
                    new_offer["Cost"] = bid_space[idx]["Cost"]
                    new_offer["Accepted"] = False
                    min_difference_utility = abs(target_utility - bid_space_utility_list[idx])

        return new_offer

    def getInitialOffer(self, product_list, recommender):
        self.time += 1
        prior_utility = 0
        product_idx = product_list[-1]

        total_selling_price = 0
        total_cost_price = 0
        for i in product_list[:-1]:
            prior_utility += recommender.cooccurance_matrix[product_idx][i] / recommender.cooccurance_matrix[product_idx][product_idx]
            total_selling_price += self.selling_price[self.product_list[i]]
            total_cost_price += self.cost_price[self.product_list[i]]

        prior_utility /= (len(product_list) - 1)

        initial_discount = min((1-prior_utility), self.max_initial_discount_rate)*(total_selling_price - total_cost_price)
        initial_offer = {"Bundle" : product_list, "Cost" : total_selling_price - initial_discount + self.selling_price[self.product_list[product_idx]], "Accepted" : False}

        return initial_offer

class Buyer:
    def __init__(self, no_of_products):
        self.MOMP_lst = [0] * no_of_products
        self.MCLP_lst = [0] * no_of_products

    def initialUtility(self, recommender, product_idx, initial_item_idx):
        return recommender.lift[product_idx][initial_item_idx]

    def utility(self, proposed_offer, prev_offer, recommender):
        proposed_bundle = proposed_offer["Bundle"]
        if proposed_bundle == prev_offer["Bundle"]:
            # bundle not changed but cost changed
            for idx in proposed_bundle:
                self.MOMP_lst[idx] += 1
        else:
            # bundle changed"
            for idx in proposed_bundle:
                    self.MOMP_lst[idx] += 1

            for idx in prev_offer["Bundle"]:
                if idx not in proposed_bundle:
                    self.MCLP_lst[idx] +=1

        # Use MOMP, MCLP, lift value for the offered items to calculate the buyer utility
        lift_sum = 0
        for idx in proposed_bundle:
            lift_sum += recommender.lift[product_idx][idx]

        lift_avg = lift_sum/len(proposed_bundle)
        utility = lift_avg \
                + sum([self.MOMP_lst[i] for i in proposed_bundle])/len(proposed_bundle) \
                - sum([self.MCLP_lst[i] for i in proposed_bundle])/len(proposed_bundle)

        return utility

class RecommenderSystem:
    def __init__(self, cooccurance_matrix):
        self.cooccurance_matrix = cooccurance_matrix

    def getInitialBundleRecommendation(self, product_idx):
        mx = -math.inf
        pos = -1
        for i in range(len(self.cooccurance_matrix[product_idx])):
            if mx < self.cooccurance_matrix[product_idx][i] and i != product_idx:
                mx = self.cooccurance_matrix[product_idx][i]
                pos = i

        return pos

    def getListOfPossibleItems(self, product_idx):
           recommendations = np.argsort(self.cooccurance_matrix[product_idx])[::-1]
           return recommendations[1:3]

def printMenu(product_list, product_idx, bundle_idx, offer, cost):

    '''
    Prints the user interface menu

    Parameters:
        product_list    - list of the entire product base
        product_idx     - the index of the product the buyer wishes to buy
        bundle_idx      - list of indices of items in the bundle
        offer           - dictionary of the offer being made
        cost            - list with the cost of the entire product base

    Returns:
        None
    '''

    print("\nPeople who buy %s also buy %s" % (product_list[product_idx], ", ".join([product_list[idx] for idx in bundle_idx])))
    print("\nOffer -> %s along with %s at a cost of %f" % (", ".join([product_list[idx] for idx in bundle_idx]), product_list[product_idx], offer["Cost"]))
    print("\nTotal amount saved = %f" % (cost[product_list[product_idx]] + sum([cost[product_list[i]] for i in bundle_idx]) - offer["Cost"]))

def getProduct(product_list):

    '''
    Get the details of the product that the buyer wishes to buy

    Parameters:
        product_list    - list of the entire product base

    Returns:
        product_name    - name of the product that the buyer wishes to buy
        product_idx - 1 - index of the product that the buyer wishes to buy
    '''

    product_idx = int(input("\nChoose an item between 1 and %d: " % len(product_list)))
    product_name = product_list[product_idx-1]
    return product_name, (product_idx-1)

def getProductIndex(product_list, product_names):
    product_name_list = product_names.split(',')
    idx_lst = []
    for j in range(len(product_name_list)):
        product_name = product_name_list[j]
        for i in range(len(product_list)):
            if product_list[i] == product_name:
                idx_lst.append(i)
                break
    return idx_lst

def getData():

    '''
    Load the product details and list values for the recommender system

    Parameters:
        None

    Returns:
        product_list        - list of the entire product base
        selling_price       - list with the selling price of the entire product base
        cost_price          - list with the cost price of the entire product base
        cooccurance_matrix  - the cooccurance matrix of the recommendation system
    '''

    data = pickle.load(open("./data.pkl", "rb"))

    return data["items"], data["selling_price"], data["cost_price"], data["cooccurance_matrix"],

def getOffer(agent, buyer, recommender, selling_price, product_list, proposed_offer, prev_offer):

    '''
    Create a new offer during the negotiation

    Parameters:
        agent           - the agent participating in the negotiation
        buyer           - the buyer participating in the negotiation
        recommender     - the recommedation system used by the agent
        selling_price   - list with the selling price of the entire product base
        product_list    - list of the entire product base
        proposed_offer  - details of the bundle that the user desires
        prev_offer      - previous offer made by the agent

    Returns:
        new_offer       - details of the bundle that the agent desires
    '''

    # prev_offer is None when negotiation has not begun
    if  not prev_offer:
        product_idx = proposed_offer["Bundle"][-1]
        initial_item_idx = recommender.getListOfPossibleItems(product_idx)
        initial_offer = agent.getInitialOffer(np.append(initial_item_idx, product_idx), recommender)
        agent.prev_agent_offers_utility_list.append(agent.utility(initial_offer, recommender))
        return initial_offer

    else:
        agent.prev_agent_offers_list.append(prev_offer)
        buyer_utility = min(1, agent.opponentModel(proposed_offer, recommender))
        agent_utility = agent.utility(proposed_offer, recommender)
        print("Agent Utility : ", agent_utility)
        print("Buyer Utility : ", buyer_utility)
        # Use the TKI method from Koley's/Fujita's paper to provide a new offer
        target_utility = agent.TKI(buyer_utility, agent_utility)
        print("Target Utility : ", target_utility)
        bid_space = agent.getBidSpace(proposed_offer, target_utility, recommender, prev_offer)
        new_offer = agent.acceptanceModel(bid_space, proposed_offer, target_utility, recommender, agent_utility)
        agent.prev_agent_offers_utility_list.append(agent.utility(new_offer, recommender))
        return new_offer

def negotiation2(agent, buyer, cooccurance_matrix, product_list, selling_price, product_idx):

    '''
    The logic of the negotiation and its flow

    Parameters:
        agent               - the agent participating in the negotiation
        buyer               - the buyer participating in the negotiation
        cooccurance_matrix  - the cooccurance matrix of the recommendation system
        product_list        - list of the entire product base
        selling_price       - list with the selling price of the entire product base
        product_idx         - index of the product that the buyer wishes to buy

    Returns:
        None
    '''

    recommender = RecommenderSystem(cooccurance_matrix)
    offer = None
    proposed_offer = {"Bundle" : [product_idx], "Cost" : None}
    accept = False
    reject = False
    while not accept and not reject:
        offer = getOffer(agent, buyer, recommender, selling_price, product_list, proposed_offer, offer)
        bundle_idx = offer["Bundle"][:-1]
        if offer["Accepted"]:
            print("Accepted. Proceeding to payment with %s and %s" % (product_list[product_idx], ", ".join([product_list[idx] for idx in bundle_idx])))
            accept = True
        else:
            printMenu(product_list, product_idx, bundle_idx, offer, selling_price)
            while True:
                inp = int(input("\nType -> 1 : Accept, 2 : Reject, 3 : New offer\n"))
                if inp == 1:
                    print("Thank You. Proceeding to payment with %s and %s" % (product_list[product_idx], ", ".join([product_list[idx] for idx in bundle_idx])))
                    accept = True
                    break
                elif inp == 2:
                    print("Proceeding to payment with only %s" % (product_list[product_idx]))
                    reject = True
                    break
                elif inp == 3:
                    possible_items_idx = recommender.getListOfPossibleItems(product_idx)
                    print(product_list[product_idx], " Price => Rs.", selling_price[product_list[product_idx]])
                    print("Possible items : ")
                    for i in range(len(possible_items_idx)):
                        print(i+1, " : ", product_list[possible_items_idx[i]], " Price => Rs.", selling_price[product_list[possible_items_idx[i]]])
                    proposed_item_idx = input("Enter new items: number between 1 and %d(other than product index): " % len(possible_items_idx))
                    proposed_item_idx = [possible_items_idx[int(i)-1] for i in proposed_item_idx.split(" ")]

                    proposed_cost = int(input("Enter cost of the new bundle: "))
                    proposed_offer["Bundle"] = np.append(proposed_item_idx, product_idx)
                    proposed_offer["Cost"] = proposed_cost
                    break
                else:
                    print("Wrong option. Please choose again.")

        first_offer = False

def negotiation(agent, buyer, cooccurance_matrix, product_list, selling_price, product_idx, offer, proposed_offer):

    '''
    The logic of the negotiation and its flow

    Parameters:
        agent               - the agent participating in the negotiation
        buyer               - the buyer participating in the negotiation
        cooccurance_matrix  - the cooccurance matrix of the recommendation system
        product_list        - list of the entire product base
        selling_price       - list with the selling price of the entire product base
        product_idx         - index of the product that the buyer wishes to buy

    Returns:
        None
    '''

    recommender = RecommenderSystem(cooccurance_matrix)
    offer = getOffer(agent, buyer, recommender, selling_price, product_list, proposed_offer, offer)
    return offer

if __name__ == "__main__":
    product_list, selling_price, cost_price, cooccurance_matrix = getData()
    product_name, product_idx = getProduct(product_list)
    agent = Agent(product_list, cost_price, selling_price, max_initial_discount_rate=0.3, min_profit_margin = 0.3)
    buyer = Buyer(len(product_list))
    negotiation2(agent, buyer, cooccurance_matrix, product_list, selling_price, product_idx)
