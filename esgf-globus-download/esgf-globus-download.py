#!/usr/bin/env python
from __future__ import print_function
import requests
import xml.etree.ElementTree as ET
import sys
import argparse
import os
import ast

from random import SystemRandom
from uuid import uuid4

# GLOBUS FUNCS

# Revised version by Matt Pritchard, CEDA/STFC to work with globus-cli

def listEndpoints(gendpointDict):

    endNames = gendpointDict.keys()
    print("Endpoints involved:")
    for thisEndName in endNames:
        print(thisEndName)


def getFiles(gendpointDict, uendpoint, username, upath):

    label = str(uuid4())

    endNames = gendpointDict.keys()

    for thisEndName in endNames:

        fileList = gendpointDict[thisEndName]

        cryptogen = SystemRandom()
        transferFile = '/tmp/transferList_' + thisEndName + '_' + str(cryptogen.randint(1,9999)) + '.txt'
        file = open(transferFile, 'w')

        for thisFile in fileList:

            basename = os.path.basename(thisFile)

            if upath[-1] != '/':
                basename = '/' + basename

            remote = thisFile
            local = upath + basename

            file.write(remote + ' ' + local + '\n')

        file.close()

        os.system("globus transfer "+thisEndName+" "+uendpoint+" --batch --label \"CLI Batch\" < "+transferFile)

        os.remove(transferFile)

    return

# ESGF SEARCH FUNCS

# API AT: https://github.com/ESGF/esgf.github.io/wiki/ESGF_Search_REST_API#results-pagination

def esgf_search(server="https://esgf-node.llnl.gov/esg-search/search", files_type="Globus", distributed=False, verbose=False, format="application%2Fsolr%2Bjson", use_csrf=False, **payload):
    client = requests.session()
    payload["type"]= "File"
    if distributed:
        payload["distrib"] = "true"
    else:
        payload["distrib"] = "false"
    if use_csrf:
        client.get(server)
        if 'csrftoken' in client.cookies:
            # Django 1.6 and up
            csrftoken = client.cookies['csrftoken']
        else:
            # older versions
            csrftoken = client.cookies['csrf']
        payload["csrfmiddlewaretoken"] = csrftoken


    payload["format"] = format

    offset = 0
    numFound = 10000
    all_files = []
    #files_type = files_type.upper()
    while offset < numFound:
        payload["offset"] = offset
        url_keys = [] 
        for k in payload:
            val = payload[k]
            if isinstance(val, (list, tuple)):
                for vl in val:
                    url_keys += ["{}={}".format(k, vl)]
            else:
                url_keys += ["{}={}".format(k, val)]

        url = "{}/?{}".format(server, "&".join(url_keys))
        r = client.get(url)
        resp = r.json()["response"]
        numFound = int(resp["numFound"])
        resp = resp["docs"]
        offset += len(resp)
        for d in resp:
            if verbose:
                for k in d:
                    print("{}: {}".format(k,d[k]))
            url = d["url"]
            for f in d["url"]:
                sp = f.split("|")
                if sp[-1] == files_type:
                    all_files.append(sp[0].split(".html")[0])
    return sorted(all_files)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = \
        '''To use this script, you must have the Globus Command Line Interface
        tools installed locally (see https://docs.globus.org/cli/)
        The host where you install these tools does
        NOT need to be one of the endpoints in the transfer.
        This script makes use of the Globus CLI 'transfer' command.
        You need to ensure the endpoints involved are activated, see "Endpoints
        to be activated" in output (use "globus endpoint activate")
        By default, the transfer command will:
        - verify the checksum of the transfer
        - encrypt the transfer
        - and delete any fies at the user endpoint with the same name.''',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter
            )
    globus  = parser.add_argument_group("Globus related keywords")
    search  = parser.add_argument_group("Search related keywords")
    globus.add_argument('-e', '--user-endpoint', type=str, help='endpoint you wish to download files to', required=True)
    globus.add_argument('-u', '--username', type=str, help='your Globus username', required=True)
    globus.add_argument('-p', '--path', type=str, help='the path on your endpoint where you want files to be downloaded to', default='/~/')
    globus.add_argument('-l', '--list-endpoints', help='List the endpoints to be activated and exit (no transfer attempted)', action='store_true')
    default_search_keys = {
        'variable': "tas",
        'experiment_id': "historical",
        'frequency': "mon",
        'institution_id': "NASA-GISS"
    }
    search.add_argument('-s', '--search-keywords', type=ast.literal_eval, help="dictionary with search keys", default=default_search_keys)
    search.add_argument('-d', '--distributed', action='store_true', help="search all nodes, not just local", default=False)
    search.add_argument("-V", "--verbose", action="store_true", default=False)
    search.add_argument("-n", "--node", help="search node", default="https://esgf-node.llnl.gov/esg-search/search")
    parser._optionals.title = 'required and optional arguments'
    parser.add_argument("-y","--no_question", help="Do not stop answers yes to all question", action="store_true", default=False)

    args = parser.parse_args()

    username = args.username
    uendpoint = args.user_endpoint
    upath = args.path
    listonly = args.list_endpoints

    if '/' in uendpoint:
        print("Do not include the download path in the endpoint name, please use the -p option")
        sys.exit()
    if '#' in upath:
        print("The '#' character is invalid in your path, please re-enter")
        sys.exit()
    if upath[0] != '/' and upath != '/~/':
        upath = '/' + upath

    verbose = args.verbose
    distributed = args.distributed

    #files = esgf_search(verbose=verbose, variable="tas", experiment_id="historical", frequency="mon", institution_id="NASA-GISS")
    #files = esgf_search(verbose=verbose, variable="ta", experiment_id="amip", frequency="mon", institution_id="NASA-GISS")
    #files = esgf_search(verbose=verbose, variable="pr", experiment_id="amip", frequency="mon", institution_id="NASA-GISS")
    #files = esgf_search(verbose=verbose, variable="cl", experiment_id="amip", frequency="mon", institution_id="NASA-GISS", files_type="Globus")
    files = []
    
    files += esgf_search(server=args.node, distributed=args.distributed, verbose=verbose, files_type="Globus", **args.search_keywords)

    print("Search resulted in: {} files\n".format(len(files)))
    if len(files) > 10:
        print("First 5 files:\n{}".format("\n".join(files[:5])))
        print("[...]\nLast 5 files:\n{}".format("\n".join(files[-5:])))
    else:
        print("Files:\n{}".format("\n".join(files)))


    if not args.no_question:
        cont = input("Do you wish to continue [y]/n?")
    else:
        cont = 'y'
    if cont.strip().lower() != "y":
        print("Bye")
        sys.exit(1)

    files_dict = {}
    for f in files:
        sp = f.split(":")[-1]
        slash = sp.find("/")
        dataset = sp[:slash]
        pth = sp[slash:]
        if not dataset in files_dict:
            files_dict[dataset] = set([pth])
        else:
            files_dict[dataset].add(pth)
    gendpointDict = files_dict
    if (listonly):
        listEndpoints(gendpointDict)
    else:
        getFiles(gendpointDict, uendpoint, username, upath)
