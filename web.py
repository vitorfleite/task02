#!/usr/bin/env python

import flask
import time
import requests
import hmac
import hashlib
import json
import uuid


class Const:
    SUMSUB_SECRET_KEY = "4R5P8VQZLvw8WQCPXsJyEzTKdEt2pCt8"  
    SUMSUB_APP_TOKEN = "tst:xTD0Tk5j6YNA3Bg1zoAAnOX2.dE5twIo6nLxHI8IEfUaVMdJ4wzoL7SNq" 
    SUMSUB_TEST_BASE_URL = "https://test-api.sumsub.com" 


CONST = Const()
applicantId = 0
imageId = 0

def createApplicant():
# https://developers.sumsub.com/api-reference/#creating-an-applicant
    global applicantId
    body = {"externalUserId": str(uuid.uuid4())}
    headers = {'Content-Type': 'application/json',
               'Content-Encoding': 'utf-8'
               }
    resp = sign_request(requests.Request('POST', 'https://test-api.sumsub.com/resources/applicants?levelName=Basic KYC',
                                         data = json.dumps(body),
                                         headers=headers
                                         ))
    s = requests.Session()
    ourresponse = s.send(resp)
    print(ourresponse.json())
    applicantId = (ourresponse.json()['id'])
    print('The applicant was successfully created:', applicantId)
    return applicantId


def addDocument():
# https://developers.sumsub.com/api-reference/#adding-an-id-document
    global imageId, applicantId
    with open('img.jpg', 'wb') as handle:
        response = requests.get('https://fv2-1.failiem.lv/thumb_show.php?i=gdmn9sqy&view', stream=True)
        if not response.ok:
            print(response)

        for block in response.iter_content(1024):
            if not block:
                break
            handle.write(block)
    payload = {"metadata": '{"idDocType":"PASSPORT", "country":"USA"}'}
    resp = sign_request(
        requests.Request('POST',  CONST.SUMSUB_TEST_BASE_URL+'/resources/applicants/'+applicantId+'/info/idDoc',
                         data=payload,
                         files=[('content', open('img.jpg', 'rb'))]
                         ))
    sw = requests.Session()
    ourresponse = sw.send(resp)
    imageId = (ourresponse.headers['X-Image-Id'])
    print('Identifier of the added document:', imageId)



def testEnviroment():
# https://developers.sumsub.com/api-reference/#testing-on-the-test-environment
    global applicantId
    body = {"reviewAnswer" : "GREEN",
            "rejectLabels" : []
            }
    headers = {'Content-Type': 'application/json',
               'Content-Encoding': 'utf-8'
               }
    resp = sign_request(requests.Request('POST', CONST.SUMSUB_TEST_BASE_URL+'/resources/applicants/'+applicantId+'/status/testCompleted',
                                         data = json.dumps(body),
                                         headers=headers
                                         ))
    s = requests.Session()
    ourresponse = s.send(resp)
    print(ourresponse.json())


def sign_request(request: requests.Request) -> requests.PreparedRequest:
    prepared_request = request.prepare()
    now = int(time.time())
    method = request.method.upper()
    path_url = prepared_request.path_url  # includes encoded query params
    # could be None so we use an empty **byte** string here
    body = b'' if prepared_request.body is None else prepared_request.body
    if type(body) == str:
        body = body.encode('utf-8')
    data_to_sign = str(now).encode('utf-8') + method.encode('utf-8') + path_url.encode('utf-8') + body
    # hmac needs bytes
    signature = hmac.new(
        CONST.SUMSUB_SECRET_KEY.encode('utf-8'),
        data_to_sign,
        digestmod=hashlib.sha256
    )
    prepared_request.headers['X-App-Token'] = CONST.SUMSUB_APP_TOKEN
    prepared_request.headers['X-App-Access-Ts'] = str(now)
    prepared_request.headers['X-App-Access-Sig'] = signature.hexdigest()
    return prepared_request

def getAccessToken():
# https://developers.sumsub.com/api-reference/#access-tokens-for-sdks
    global applicantId
    params = {"userId": '6013f8c5824e5b0009deceb3', "ttlInSecs": '600'}
    headers = {'Content-Type': 'application/json',
               'Content-Encoding': 'utf-8'
               }
    resp = sign_request(requests.Request('POST', CONST.SUMSUB_TEST_BASE_URL+'/resources/accessTokens',
                                         params=params,
                                         headers=headers
                                         ))
    s = requests.Session()
    ourresponse = s.send(resp)
    token = (ourresponse.json()['token'])
    print('Token:', token)
    return token


 # Such actions are presented below:
 # 1) Creating an applicant
 # 2) Adding a document to the applicant
 # 3) Testing on the test environment
 # 4) Access tokens for SDKs



# Create the application.
APP = flask.Flask(__name__)


@APP.route('/')

def index():
    """ Displays the index page accessible at '/'
    """
    applicantId = createApplicant()
    addDocument()
    testEnviroment()
    token = getAccessToken()
    data = {'token': token}
    return flask.render_template('index.html', data = data)


if __name__ == '__main__':
    APP.debug=True
    APP.run()