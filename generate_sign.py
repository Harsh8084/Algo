from cryptography.hazmat.primitives.asymmetric import ed25519
from urllib.parse import urlparse, urlencode
import urllib.parse
import json
import requests

params = {
    "exchange": "c2c2",
}
payload = {}
method = "GET"
endpoint = "/trade/api/v2/coins"
endpoint += ('&', '?')[urlparse(endpoint).query == ''] + urlencode(params)

secret_key = "api_key"
api_key = "secret_key"

def get_signature(method, endpoint, payload, params, api_key, secret_key):
    unquote_endpoint = endpoint
    if method == "GET" and len(params) != 0:
        unquote_endpoint = urllib.parse.unquote_plus(endpoint)

    signature_msg = method + unquote_endpoint + json.dumps(payload, separators=(',', ':'), sort_keys=True)

    print("Signature Message:", signature_msg)  # Debugging line

    request_string = bytes(signature_msg, 'utf-8')
    secret_key_bytes = bytes.fromhex(secret_key)
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(secret_key_bytes)
    signature_bytes = private_key.sign(request_string)
    signature = signature_bytes.hex()
    
    print("Signature Bytes:", signature_bytes)  # Debugging line
    print("Signature Hex:", signature)  # Debugging line

    return signature

def get_coins(signature, api_key, method, params, payload, endpoint):
    url = "https://coinswitch.co" + endpoint

    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-SIGNATURE': signature,
        'X-AUTH-APIKEY': api_key
    }
    print("URL:", url)  # Debugging line
    print("Headers:", headers)  # Debugging line
    response = requests.request(method, url, headers=headers, json=payload)
    return response.json()

res = get_signature(method, endpoint, payload, params, api_key, secret_key)
print_coins = get_coins(res, api_key, method, params, payload, endpoint)
print(print_coins)
