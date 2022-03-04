#! /usr/local/bin/python3

import os, datetime, progressbar, argparse, sys, json
from urllib import response
import urllib.request, urllib.parse

parser=argparse.ArgumentParser("Sync time entries between two Harvest account, i.e your Witted and Mavericks Harvest accounts")
parser.add_argument('-a','--source', required=True, type=str, help='Source Harvest account ID')
parser.add_argument('-b','--destination', required=True, type=str, help='Destination Harvest account ID')
parser.add_argument('-t','--token', required=True, type=str, help='Your Harvest personal access token. Create your token here: https://id.getharvest.com/developers')
parser.add_argument('-s','--start', required=True, type=str, help='The date from to start the sync. Format: yyyy-mm-dd')
parser.add_argument('-e','--end', required=True, type=str, help='The date to end the sync, inclusive. Format: yyyy-mm-dd')
args=parser.parse_args()

def getDestinationProjectId( sourceProjectId, mapping ):

    try:
        for project in mapping:
            if sourceProjectId == project['source_project_id']:
                return project['destination_project_id']
    except Exception as e:

        print("Error in getting project id! - "+ str(e))

    return None

def getDestinationTaskId( sourceProjectId, sourceTaskId, mapping ):
    
    try:
        for project in mapping:
            if sourceProjectId == project['source_project_id']:
                for task in project['tasks']:
                    if sourceTaskId == task['source_task_id']:
                        return task['destination_task_id']
    except Exception as e:

        print("Error in getting task id! - "+ str(e))

    return None

def isThereDuplicateEntries (entry, destinationEntries):
    #TODO
    return False

url = "https://api.harvestapp.com/v2/time_entries" + "?from=" + args.start + "&to=" + args.end

headers_source = {
    "User-Agent": "Harvest Sync App",
    "Authorization": "Bearer " + args.token,
    "Harvest-Account-ID": args.source
}

headers_destination = {
    "User-Agent": "Harvest Sync App",
    "Authorization": "Bearer " + args.token,
    "Harvest-Account-ID": args.destination,
    "Content-Type": "application/json; charset=utf-8"
}

print("Fetching from Source Harvest...")
get_request_source = urllib.request.Request(url=url, headers=headers_source)
get_response_source = urllib.request.urlopen(get_request_source, timeout=5)

get_request_destination = urllib.request.Request(url=url, headers=headers_destination)
get_response_destination = urllib.request.urlopen(get_request_destination, timeout=5)

if get_response_source.getcode() == 200:

    try:

        print("Sending entries to Destination Harvest...")
        response_source = get_response_source.read().decode("utf-8")
        jsonResponse_source = json.loads(response_source)

        response_destination = get_response_destination.read().decode("utf-8")
        jsonResponse_destination = json.loads(response_destination)

        bar = progressbar.ProgressBar(maxval=len(jsonResponse_source['time_entries']), \
        widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])

        with open(os.getcwd()+"/mapping.json") as f:

            mapping = json.loads(f.read())
            count = 0
            bar.start()

            for entry in jsonResponse_source['time_entries']:

                count = count+1
                bar.update(count)
                
                try:
                    
                    destination_project_id = getDestinationProjectId(entry['project']['id'], mapping)
                    destination_task_id = getDestinationTaskId(entry['project']['id'], entry['task']['id'], mapping)

                    if destination_project_id and destination_task_id is not None:

                        payload = json.dumps({"project_id":destination_project_id,"task_id":destination_task_id,"spent_date":entry['spent_date'],"hours":entry['hours'],"notes": entry['notes']})
                        payload_bytes = payload.encode('utf-8')

                        if not isThereDuplicateEntries(entry, jsonResponse_destination):

                            post_request = urllib.request.Request(url=url, headers=headers_destination, method="POST", data=payload_bytes)
                            post_response = urllib.request.urlopen(post_request, timeout=5)

                except Exception as e:

                    print("Oops! - "+ str(e))

        f.close()
        bar.finish()
        print("Done!")

    except Exception as e:

        print("Oops! - "+ str(e))
else:
    print ("Retreiving source time entries failed - " + str(get_response_source.getcode()))

