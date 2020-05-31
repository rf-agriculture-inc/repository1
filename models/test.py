"""TESTS"""

from .connector import MagentoAPI


def test_magento_connection(self):
    """Test call to check connection."""
    try:
        api_connector = MagentoAPI(self)
        res = api_connector.test_connection()
        if res.ok:
            title = "Connection Test Succeeded!"
            message = "Everything seems properly set up!"
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': title,
                    'message': message,
                    'sticky': False,
                }
            }
        else:
            raise Exception(res.text)
    except Exception as e:
        # raise UserError(f"Connection Test Failed! Here is what we got instead:\n{e}")
        print(f"Connection Test Failed! Here is what we got instead:\n{e}")

def test_search_customers(self):
    model = 'customers'
    # filters = [{
    #     "field": "email",
    #     "value": "daniel@redflagproducts.com",
    #     "condition_type": "eq"
    # }]

    filters = [{
        "field": "id",
        "value": "1",
        "condition_type": "eq"
    }]

    api_connector = MagentoAPI(self)
    response = api_connector.search(model, filters)
    print(response)
    # print(response.text)

def test_get_orders(self):
    model = 'orders'
    filters = [{
        "field": "id",
        "value": "100",
        "condition_type": "eq"
    }]
    api_connector = MagentoAPI(self)
    response = api_connector.get(model, filters)
    print(response)
    print(response['search_criteria'])
    print(response['total_count'])
    # print(response.text)

def test_put_customer(self):
    payload = {
        "customer": {
            'id': 1,
            "email": "test@test.com",
            "firstname": "Jack3",
            "lastname": "Daniels3",
            "storeId": 1,
            "websiteId": 1,
        }
    }

def test_post_customer(self):
    payload = {
        "customer": {
            "email": "ready.mat28@example.com",
            "firstname": "Ready",
            "lastname": "Mat"
        }
    }

