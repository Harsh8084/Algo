import hmac
import hashlib
import json
import time
import requests
from datetime import datetime, timedelta
import pandas as pd

class CoinDCX:
    def __init__(self, api_key, secret):
        self.api_key = api_key
        self.secret = secret
        self.secret_bytes = bytes(secret, encoding='utf-8')

    def _get_timestamp(self):
        return int(round(time.time() * 1000))

    def _generate_signature(self, body):
        return hmac.new(self.secret_bytes, body.encode(), hashlib.sha256).hexdigest()


    def cancel_all_open_orders(self):
        url = "https://api.coindcx.com/exchange/v1/derivatives/futures/positions/cancel_all_open_orders"
        body = json.dumps({"timestamp": self._get_timestamp()}, separators=(',', ':'))
        signature = self._generate_signature(body)
        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': self.api_key,
            'X-AUTH-SIGNATURE': signature
        }
        response = requests.post(url, data=body, headers=headers)
        return response.json()

    def get_position_id(self):
        url = "https://api.coindcx.com/exchange/v1/derivatives/futures/positions"
        body = json.dumps({
            "timestamp": self._get_timestamp(),
            "page": "1",
            "size": "10"
        }, separators=(',', ':'))
        signature = self._generate_signature(body)
        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': self.api_key,
            'X-AUTH-SIGNATURE': signature
        }
        response = requests.post(url, data=body, headers=headers)
        data = response.json()
        print(data)
        if data:
            first_item = data[0]
            return first_item['id']
        else:
            return None

    def exit_open_position(self, position_id):
        url = "https://api.coindcx.com/exchange/v1/derivatives/futures/positions/exit"
        body = json.dumps({
            "timestamp": self._get_timestamp(),
            "id": str(position_id)
        }, separators=(',', ':'))
        signature = self._generate_signature(body)
        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': self.api_key,
            'X-AUTH-SIGNATURE': signature
        }
        response = requests.post(url, data=body, headers=headers)
        return response.json()

    def execute_order(self, side, price):
        url = "https://api.coindcx.com/exchange/v1/derivatives/futures/orders/create"
        body = json.dumps({
            "timestamp": self._get_timestamp(),
            "order": {
                "side": side,
                "pair": "B-ETH_USDT",
                "order_type": "limit_order",
                "price": str(price),
                "total_quantity": 0.033,
                "leverage": 5,
                "notification": "email_notification",
                "time_in_force": "good_till_cancel",
                "hidden": False,
                "post_only": False
            }
        }, separators=(',', ':'))
        signature = self._generate_signature(body)
        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': self.api_key,
            'X-AUTH-SIGNATURE': signature
        }
        response = requests.post(url, data=body, headers=headers)
        return response.json()

    def set_tp_sl(self, position_id, take_profit_price, stop_loss_price):
        url = "https://api.coindcx.com/exchange/v1/derivatives/futures/positions/create_tpsl"
        body = json.dumps({
            "timestamp": self._get_timestamp(),
            "id": position_id,
            "take_profit": {
                "stop_price": str(take_profit_price),
                "limit_price": str(take_profit_price),
                "order_type": "take_profit_limit"
            },
            "stop_loss": {
                "stop_price": str(stop_loss_price),
                "limit_price": str(stop_loss_price),
                "order_type": "stop_limit"
            }
        }, separators=(',', ':'))
        signature = self._generate_signature(body)
        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': self.api_key,
            'X-AUTH-SIGNATURE': signature
        }
        response = requests.post(url, data=body, headers=headers)
        return response.json()

    def get_candlestick_data(self, start_epoch, end_epoch):
        url = "https://public.coindcx.com/market_data/candlesticks"
        query_params = {
            "pair": "B-ETH_USDT",
            "from": start_epoch,
            "to": end_epoch,
            "resolution": "15m",
            "pcode": "f"
        }
        response = requests.get(url, params=query_params)
        if response.status_code == 200:
            return response.json()
        else:
            return f"Error: {response.status_code}, {response.text}"

def main():
    # Initialize the CoinDCX class with your API key and secret
    api_key = 'ea28fa11c8193a0cd8e606428bcbc6d437baf36e96a1e8c9'
    secret = '61e9fdb944f218281a2e1eba75af1dc9e3f62af89b47d04c13c5900d3a980959'
    coindcx = CoinDCX(api_key, secret)

    # Cancel all open orders if any
    coindcx.cancel_all_open_orders()

    # Cancel ongoing position if any
    position_id = coindcx.get_position_id()
    if position_id:
        coindcx.exit_open_position(position_id)

    # Get data for analysis
    start_epoch, end_epoch = get_exact_epoch_times()  # This function should be defined in the same or another module
    data = coindcx.get_candlestick_data(start_epoch, end_epoch)

    if isinstance(data, dict) and 'data' in data:
        candles = data['data']
        
        if len(candles) > 1:
            candles = candles[:-1]
        
            df = pd.DataFrame(candles)
        
            red_candles = 0
            for i in range(-3, 0):
                if df.iloc[i]['close'] < df.iloc[i]['open']:
                    red_candles += 1
        
            side = 'sell' if red_candles >= 2 else 'buy'
            entry_price = df.iloc[-1]['close']
            print(f"Executing {side} trade at {entry_price}")
        
            # Execute the order
            order_response = coindcx.execute_order(side, entry_price)
        
            # Check order status and set TP and SL
            time.sleep(600)  # Wait for 10 seconds before checking the status
            positions = coindcx.check_order_status()  # Method needs to be added to CoinDCX
            
            if positions and isinstance(positions, list) and len(positions) > 0:
                position = positions[0]
                if position['avg_price'] > 0:
                    print(f"Order filled. Position active with avg price: {position['avg_price']}")
                    take_profit_price = entry_price * 1.004 if side == 'buy' else entry_price * 0.996
                    stop_loss_price = entry_price * 0.98 if side == 'buy' else entry_price * 1.02
                    coindcx.set_tp_sl(position['id'], take_profit_price, stop_loss_price)
                else:
                    print("Order not filled yet.")
            else:
                print("No positions found.")
    else:
        print("Error retrieving data or no data available")

if __name__ == "__main__":
    main()
