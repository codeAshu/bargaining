from flask import Flask, render_template, request
import bargain as bg
from werkzeug.serving import run_simple

# set to True to inform that the app needs to be re-created
to_reload = False
offer = None

def get_app():
    app = Flask(__name__)
    product_list, selling_price, cost_price, cooccurance_matrix = bg.getData()
    agent = bg.Agent(product_list, cost_price, selling_price, max_initial_discount_rate=0.1, min_profit_margin = 0.3)
    buyer = bg.Buyer(len(product_list))
    offer_history = list()

    @app.route('/', methods=['GET'])
    def index():
        print("RELOADED")
        global offer
        offer = None
        offer_history = list()
        global to_reload
        to_reload = True
        return render_template('index.html', product_list=product_list, selling_price=selling_price)

    @app.route('/first_negotiate/<string:product_name>', methods=['GET', 'POST'])
    def first_negotiate(product_name):
        global offer
        offer = None
        idx = bg.getProductIndex(product_list, product_name)[0]
        recommender = bg.RecommenderSystem(cooccurance_matrix)
        proposed_offer = {"Bundle" : [idx], "Cost" : None}
        offer = bg.negotiation(agent, buyer, cooccurance_matrix, product_list, selling_price, idx, offer, proposed_offer)
        offer_history.append(offer)
        bundle_idx = offer["Bundle"][:-1]
        offer["Cost"] = round(offer["Cost"])
        if offer["Accepted"]:
            product_idx = offer["Bundle"][-1]
            total_selling_price = 0
            for i in offer["Bundle"]:
                total_selling_price += selling_price[product_list[i]]
            return render_template('accept.html', product_list=product_list, product_idx=idx, product_names=','.join([product_list[idx] for idx in bundle_idx]), amount_saved=total_selling_price - offer["Cost"], cost=offer["Cost"], offer_history=offer_history)
        else:
            product_idx = offer["Bundle"][-1]
            amount_saved = selling_price[product_list[product_idx]] + sum([selling_price[product_list[i]] for i in bundle_idx]) - offer["Cost"]
            return render_template('negotiate.html', product_list=product_list, product_idx=product_idx, selling_price=selling_price, amount_saved=round(amount_saved), offer=offer, possible_items = recommender.getListOfPossibleItems(product_idx), product_names=','.join([product_list[i] for i in offer['Bundle']]), offer_history=offer_history)

    @app.route('/negotiate/<string:product_name>', methods=['POST'])
    def rest_negotiate(product_name):
        global offer
        print(request.form)
        idx = [int(i) for i in request.form if i != 'cost']
        idx.append(bg.getProductIndex(product_list,product_name)[0])
        recommender = bg.RecommenderSystem(cooccurance_matrix)
        proposed_offer = {"Bundle" : idx, "Cost" : int(request.form['cost'])}
        offer_history.append(proposed_offer)
        offer = bg.negotiation(agent, buyer, cooccurance_matrix, product_list, selling_price, idx, offer, proposed_offer)
        offer_history.append(offer)
        bundle_idx = offer["Bundle"][:-1]
        offer["Cost"] = round(offer["Cost"])
        if(offer["Cost"] <= proposed_offer["Cost"]):
            offer["Accepted"] = True
            
        if offer["Accepted"]:
            product_idx = offer["Bundle"][-1]
            total_selling_price = 0
            for i in offer["Bundle"]:
                total_selling_price += selling_price[product_list[i]]
            return render_template('accept.html', product_list=product_list, product_idx=product_idx, product_names=','.join([product_list[idx] for idx in bundle_idx]), amount_saved=total_selling_price - offer["Cost"], cost=offer["Cost"], offer_history=offer_history)
        else:
            product_idx = offer["Bundle"][-1]
            amount_saved = selling_price[product_list[product_idx]] + sum([selling_price[product_list[i]] for i in bundle_idx]) - offer["Cost"]
            return render_template('negotiate.html', product_list=product_list, product_idx=product_idx, selling_price=selling_price, amount_saved=amount_saved, offer=offer, possible_items = recommender.getListOfPossibleItems(product_idx), product_names=','.join([product_list[i] for i in offer['Bundle']]), offer_history=offer_history)

    @app.route('/accept/<string:product_names>/<int:accept>/<int:cost>/<int:amount_saved>')
    def accept(product_names, accept, cost, amount_saved):
        indices = bg.getProductIndex(product_list, product_names)
        bundle_idx = indices[:-1]
        product_idx = indices[-1]
        if accept:
            return render_template('accept.html', product_list=product_list, product_idx=product_idx, product_names=','.join([product_list[idx] for idx in bundle_idx]), amount_saved=round(amount_saved), cost=round(cost))
        else:
            return render_template('reject.html', product=product_list[product_idx], cost=int(selling_price[product_list[product_idx]]))

    return app

class AppReloader(object):
    def __init__(self, create_app):
        self.create_app = create_app
        self.app = create_app()

    def get_application(self):
        global to_reload
        if to_reload:
            self.app = self.create_app()
            to_reload = False

        return self.app

    def __call__(self, environ, start_response):
        app = self.get_application()
        return app(environ, start_response)

application = AppReloader(get_app)

if __name__ == "__main__":
    run_simple('localhost', 8080, application,
               use_reloader=True, use_debugger=True, use_evalex=True)