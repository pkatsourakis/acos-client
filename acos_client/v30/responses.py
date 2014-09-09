# Copyright 2014,  Doug Wiegley,  A10 Networks.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import re

import acos_client.errors as ae


RESPONSE_CODES = {
    67371011: {
        '*': {
            '*': ae.Exists
        }
    },
    1023410176: {
        'DELETE': {
            '*': None
        },
        '*': {
#            '/axapi/v3/slb/service-group/': ae.NoSuchServiceGroup,
            '*': ae.NotFound
        }
    },
    1023410181: {
        'DELETE': {
            '*': None
        },
        '*': {
            '/axapi/v3/slb/service-group/.*/member/': ae.NotFound,
            '*': ae.NotFound
        }
    },
    1023475722: {
        '*': {
            '*': ae.NotFound
        }
    },
    1207959957: {
        '*': {
            '*': ae.NotFound
        }
    },
}


def raise_axapi_auth_error(response, method, api_url, headers):
    if 'authorizationschema' in response:
        if response['authorizationschema']['code'] == 401:
            if 'Authorization' in headers:
                raise ae.InvalidSessionID()
            else:
                raise ae.AuthenticationFailure()
        elif response['authorizationschema']['code'] == 403:
            raise ae.AuthenticationFailure()


def raise_axapi_ex(response, method, api_url):
    if 'response' in response and 'err' in response['response']:
        code = response['response']['err']['code']

        # Check if this is a known error code that we want to map.
        if code in RESPONSE_CODES:
            ex_dict = RESPONSE_CODES[code]
            ex = None

            # Now match against specific HTTP method exceptions
            if method in ex_dict:
                x = ex_dict[method]
            else:
                x = ex_dict['*']

            # Now try to find specific API method exceptions
            for k in x.keys():
                #if api_url.startswith(k):
                if k != '*' and re.match('^'+k, api_url):
                    ex = x[k]

            # If we get here, try for a fallback exception for this code
            if not ex and '*' in x:
                ex = x['*']

            # Alright, time to actually do something
            if ex:
                raise ex(code, response['response']['err']['msg'])
            else:
                return

        raise ae.ACOSException(code, response['response']['err']['msg'])

    raise ae.ACOSException()
