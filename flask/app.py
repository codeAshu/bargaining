from flask import Flask, render_template, url_for, request
import bargain as bg

app = Flask(__name__)
product_list, selling_price, cost_price, cooccurance_matrix = bg.getData()
offer = None
agent = bg.Agent(product_list, cost_price, selling_price, max_initial_discount_rate=0.3, min_profit_margin = 0.3)
buyer = bg.Buyer(len(product_list))

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', product_list=product_list, selling_price=selling_price)

@app.route('/first_negotiate/<string:product_name>', methods=['GET', 'POST'])
def first_negotiate(product_name):
    global offer
    offer = None
    idx = bg.getProductIndex(product_list, product_name)[0]
    recommender = bg.RecommenderSystem(cooccurance_matrix)
    proposed_offer = {"Bundle" : [idx], "Cost" : None}
    offer = bg.negotiation(agent, buyer, cooccurance_matrix, product_list, selling_price, idx, offer, proposed_offer)
    bundle_idx = offer["Bundle"][:-1]
    if offer["Accepted"]:
        product_idx = offer["Bundle"][-1]
        return "Accepted. Proceeding to payment for " + product_list[product_idx] + " along with " + ", ".join([product_list[idx] for idx in bundle_idx])
    else:
        product_idx = offer["Bundle"][-1]
        amount_saved = selling_price[product_list[product_idx]] + sum([selling_price[product_list[i]] for i in bundle_idx]) - offer["Cost"]
        return render_template('negotiate.html', product_list=product_list, selling_price=selling_price, amount_saved=amount_saved, offer=offer, possible_items = recommender.getListOfPossibleItems(product_idx), product_names=','.join([product_list[i] for i in offer['Bundle']]))

@app.route('/negotiate/<string:product_name>', methods=['POST'])
def rest_negotiate(product_name):
    global offer
    print(request.form)
    idx = [int(i) for i in request.form if i != 'cost']
    idx.append(bg.getProductIndex(product_list,product_name)[0])
    recommender = bg.RecommenderSystem(cooccurance_matrix)
    proposed_offer = {"Bundle" : idx, "Cost" : int(request.form['cost'])}
    offer = bg.negotiation(agent, buyer, cooccurance_matrix, product_list, selling_price, idx, offer, proposed_offer)
    bundle_idx = offer["Bundle"][:-1]
    if offer["Accepted"]:
        product_idx = offer["Bundle"][-1]
        return "Accepted. Proceeding to payment for " + product_list[product_idx] + " along with " + ", ".join([product_list[idx] for idx in bundle_idx])
    else:
        product_idx = offer["Bundle"][-1]
        amount_saved = selling_price[product_list[product_idx]] + sum([selling_price[product_list[i]] for i in bundle_idx]) - offer["Cost"]
        return render_template('negotiate.html', product_list=product_list, selling_price=selling_price, amount_saved=amount_saved, offer=offer, possible_items = recommender.getListOfPossibleItems(product_idx), product_names=','.join([product_list[i] for i in offer['Bundle']]))

@app.route('/accept/<string:product_names>/<float:cost>/<int:accept>')
def accept(product_names, cost, accept):
    indices = bg.getProductIndex(product_list, product_names)
    bundle_idx = indices[:-1]
    product_idx = indices[-1]
    if accept == 1:
        return "Accepted. Proceeding to payment for " + product_list[product_idx] + " along with " + ", ".join([product_list[idx] for idx in bundle_idx])
    else:
        return "Proceeding to payment with only " + product_list[product_idx]

if __name__ == "__main__":
    app.run(debug=True)