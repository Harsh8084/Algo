import hmac
import hashlib
import json
import time
from datetime import datetime
import requests

class CoinDCXAPI:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.coindcx.com/exchange/v1"

    def _generate_signature(self, body):
        secret_bytes = bytes(self.api_secret, encoding='utf-8')
        json_body = json.dumps(body, separators=(',', ':'))
        signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()
        return signature, json_body

    def _make_request(self, endpoint, body):
        signature, json_body = self._generate_signature(body)
        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': self.api_key,
            'X-AUTH-SIGNATURE': signature
        }
        response = requests.post(f"{self.base_url}/{endpoint}", data=json_body, headers=headers)
        return response.json()

    def get_user_info(self):
        body = {"timestamp": int(time.time() * 1000)}
        return self._make_request("users/info", body)

    def get_user_balance(self):
        body = {"timestamp": int(time.time() * 1000)}
        return self._make_request("users/balances", body)

    def transfer_assets(self, transfer_from, transfer_to, currency, quantity):
        body = {
            "timestamp": int(time.time() * 1000),
            "source_wallet_type": transfer_from,
            "destination_wallet_type": transfer_to,
            "currency_short_name": currency,
            "amount": quantity
        }
        return self._make_request("wallets/transfer", body)

    def create_futures_order(self, side, coin, order_type, entry_price, trade_amount, lev):
        quantity = (trade_amount * lev) / entry_price
        body = {
            "timestamp": int(time.time() * 1000),
            "order": {
                "side": side,
                "pair": coin,
                "order_type": order_type,
                "price": entry_price,
                "total_quantity": quantity,
                "leverage": lev,
                "notification": "email_notification",
                "time_in_force": "good_till_cancel",
                "hidden": False,
                "post_only": False
            }
        }
        return self._make_request("derivatives/futures/orders/create", body)

    def get_order_history(self):
        body = {
            "timestamp": int(time.time() * 1000),
            "page": "1",
            "size": "10"
        }
        return self._make_request("derivatives/futures/positions", body)

    def set_tp_sl(self, order_id, tp_price, sl_price):
        body = {
            "timestamp": int(time.time() * 1000),
            "id": order_id,
            "take_profit": {
                "stop_price": "67160.0",
                "limit_price": tp_price,
                "order_type": "take_profit_limit"
            },
            "stop_loss": {
                "stop_price": "0.271",
                "limit_price": sl_price,
                "order_type": "stop_limit"
            }
        }
        return self._make_request("derivatives/futures/positions/create_tpsl", body)

    @staticmethod
    def to_unix_timestamp_millis(dt_str):
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return int(dt.timestamp() * 1000)

    @staticmethod
    def from_unix_timestamp_millis(timestamp_millis):
        dt = datetime.fromtimestamp(timestamp_millis / 1000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def get_market_data(currency, start_time, end_time):
        url = f"https://public.coindcx.com/market_data/candles?pair={currency}&interval=15m&startTime={start_time}&endTime={end_time}"
        response = requests.get(url)
        return response.json()


api_key = 'ea28fa11c8193a0cd8e606428bcbc6d437baf36e96a1e8c9'
api_secret = '61e9fdb944f218281a2e1eba75af1dc9e3f62af89b47d04c13c5900d3a980959'
coindcx = CoinDCXAPI(api_key, api_secret)

# Example calls
print(coindcx.get_user_info())
print(coindcx.get_user_balance())
