from cryptography.hazmat.primitives.asymmetric import ed25519
from urllib.parse import urlparse, urlencode, unquote_plus
import json
import requests

method = "GET"
params = {
    "exchange": "wazirx",
}
payload = {
   # "side":"buy",
   # "symbol":"BTC/USDT",
   # "type":"limit",
   # "price":60000,
   # "quantity":0.0009,
   # "exchange":"c2c2"
}
endpoint = "/trade/api/v2/user/portfolio"
endpoint += ('&', '?')[urlparse(endpoint).query == ''] + urlencode(params)


def construct_endpoint(method, endpoint, params):
    if method == "GET" and params:
        query_string = urlencode(params)
        if urlparse(endpoint).query:
            endpoint += '&' + query_string
        else:
            endpoint += '?' + query_string
    return endpoint

def get_signature(method, endpoint, payload, secret_key):
    unquote_endpoint = unquote_plus(endpoint)

    if method == "GET":
        payload_str = json.dumps({}, separators=(',', ':'), sort_keys=True)
    else:
        payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)

    signature_msg = method + unquote_endpoint + payload_str
    print("Signature Message:", signature_msg)  # Debugging line

    request_string = bytes(signature_msg, 'utf-8')
    secret_key_bytes = bytes.fromhex(secret_key)
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(secret_key_bytes)
    signature_bytes = private_key.sign(request_string)
    signature = signature_bytes.hex()

    print("Signature Bytes:", signature_bytes)  # Debugging line
    print("Signature Hex:", signature)  # Debugging line

    return signature

def send_request(method, endpoint, params, payload, api_key, secret_key):
    endpoint = construct_endpoint(method, endpoint, params)
    signature = get_signature(method, endpoint, payload, secret_key)

    url = "https://coinswitch.co" + endpoint
    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-SIGNATURE': signature,
        'X-AUTH-APIKEY': api_key
    }

    print("Request URL:", url)  # Debugging line
    print("Headers:", headers)  # Debugging line

    response = requests.request(method, url, headers=headers, json=payload if method != "GET" else None)
    return response.json()


api_key = "api_key"
secret_key = "secret_key

response = send_request(method, endpoint, params, payload, api_key, secret_key)
response
