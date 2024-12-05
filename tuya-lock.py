###################################################################
# Author: Felipe Godoy                                            #
# Date: 2024-12-04                                                #
# Version: 1.0                                                    #
# Description:                                                    #
# This script is a Python implementation of the Tuya API to open  #
# a Tuya smart lock.                                              #
#                                                                 #
# The script uses the Tuya API to get the authentication tokens,  #
# the temporary key and open the door.                            #
###################################################################

import hashlib
import requests
import datetime
import hmac
import json

# Tuya API URL - This URL is not the same for all regions, you can get it from the Tuya Developer Platform.
API_URL = 'https://openapi.tuyaus.com'
# Client ID - You can get it from the Tuya Developer Platform
CLIENT_ID = ''
# Secret - You can get it from the Tuya Developer Platform
SECRET = ''
# Device ID - You can get it from the Tuya Developer Platform
DEVICE_ID = ''

def hmac_sha256(key, message):
  return hmac.new(
    key.encode("utf-8"), 
    message.encode("utf-8"), 
    hashlib.sha256
  ).hexdigest()

# Function to calculate the sign according to the Tuya API Documentation
def calcSign(clientId, timestamp, nonce, signStr, secret, accessToken=''):
  string = clientId + accessToken + timestamp + nonce + signStr
  # print(f'String sign raw: \n{string}\n')
  hash = hmac_sha256(secret, string)
  hashInBase64 = hash.encode('utf-8')
  signUp = hashInBase64.upper()
  return signUp

# Function to calculate the string to sign according to the Tuya API Documentation
# See more at: https://developer.tuya.com/en/docs/iot/new-singnature?id=Kbw0q34cs2e5g
def stringToSign(httpMethod, url_to_sign, body_to_sign=None):
  headerStr = ''
  body_to_sign = None if body_to_sign is None else json.dumps(body_to_sign)
  sha256 = hashlib.sha256() if body_to_sign is None else hashlib.sha256(body_to_sign.encode('utf-8'))
  string = httpMethod + '\n' + sha256.hexdigest() + '\n' + headerStr + '\n' + url_to_sign
  return string

# Function to get the basic headers for the Tuya API requests
# See more at: https://developer.tuya.com/en/docs/iot/new-singnature?id=Kbw0q34cs2e5g
def get_basic_headers(http_method, url_to_sign, access_token=None, body_to_sign=None):
  nonce = ''
  timestamp = str(int(datetime.datetime.now().timestamp() * 1000))
  signString = stringToSign(http_method, url_to_sign, body_to_sign)
  sign = calcSign(CLIENT_ID, timestamp, nonce, signString, SECRET)
  
  headers_obj = {
      'client_id': CLIENT_ID,
      'sign': sign,
      't': timestamp,
      'sign_method': 'HMAC-SHA256'
  }
  
  if access_token:
    headers_obj['access_token'] = access_token
    headers_obj['sign'] = calcSign(CLIENT_ID, timestamp, nonce, signString, SECRET, access_token)

  return headers_obj

# Function to get the authentication tokens
# See documentation: https://developer.tuya.com/en/docs/cloud/6c1636a9bd?id=Ka7kjumkoa53v
def get_authentication_tokens():
  HTTP_METHOD = 'GET'
  URL_PATH = '/v1.0/token?grant_type=1'
  FULL_URL = f'{API_URL}{URL_PATH}'
  
  try:
    headers = get_basic_headers(HTTP_METHOD, URL_PATH)
    result = requests.request(HTTP_METHOD, FULL_URL, headers=headers)
    jsonResponse = result.json()

    access_token = jsonResponse['result']['access_token']
    refresh_token = jsonResponse['result']['refresh_token']
    
    return {
      'access_token': access_token,
      'refresh_token': refresh_token
    }
  except Exception as e:
    print(f'Error: {e}')
    return None

# Function to get the temporary key to open the door without password
# See documentation: https://developer.tuya.com/en/docs/archived-documents/c6ec729dac?id=Kat26yeejknqo
def get_temporary_key(access_token, device_id):
  HTTP_METHOD = 'POST'
  URL_PATH = f'/v1.0/devices/{device_id}/door-lock/password-ticket'
  FULL_URL = f'{API_URL}{URL_PATH}'
  
  try:
    headers = get_basic_headers(HTTP_METHOD, URL_PATH, access_token=access_token)

    result = requests.request(HTTP_METHOD, FULL_URL, headers=headers)
    jsonResponse = result.json()

    ticket_id = jsonResponse['result']['ticket_id']
    ticket_key = jsonResponse['result']['ticket_key']

    return {
      'ticket_id': ticket_id,
      'ticket_key': ticket_key
    }
  except Exception as e:
    print(f'Error: {e}')
    return None

# Function to open the door using the temporary key
# See documentation: https://developer.tuya.com/en/docs/cloud/doorlock-api-remoteopen?id=Kbe2nm6j9hcsj#title-3-Unlock%20without%20a%20password
def open_tuya_lock(device_id, ticket_id, access_token):
  HTTP_METHOD = 'POST'
  URL_PATH = f'/v1.1/devices/{device_id}/door-lock/password-free/open-door'
  FULL_URL = f'{API_URL}{URL_PATH}'
  
  try:
    body = {
      'ticket_id': ticket_id,
    }
    
    headers = get_basic_headers(HTTP_METHOD, URL_PATH, body=body, access_token=access_token)
    result = requests.request(HTTP_METHOD, FULL_URL, headers=headers, json=body)
    resultJson = result.json()
    
    if resultJson['success']:
      return 'Door opened successfully'
    else:
      raise Exception('Error opening the door')
  except Exception as e:
    print(f'Error: {e}')
    return None

print('Get tokens...')
tokens = get_authentication_tokens()
print('Get temporal key...')
temporary_key = get_temporary_key(tokens['access_token'], DEVICE_ID)
print('Open door...')
result = open_tuya_lock(DEVICE_ID, temporary_key['ticket_id'], tokens['access_token'])
print(result)


    