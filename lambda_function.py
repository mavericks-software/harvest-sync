import os, json, boto3, base64
from datetime import datetime, timedelta
from urllib import response
import urllib.request, urllib.parse
from botocore.exceptions import ClientError


def get_token():

    secret_name = "arn:aws:secretsmanager:eu-north-1:919752674607:secret:harvest_token-MVTrdu"
    region_name = "eu-north-1"
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        print("Retrieving API token")
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )

    except ClientError as e:
      
        if e.response['Error']['Code'] == 'AccessDeniedException':
            print("Error getting token: " + e.response['Error']['Code'])
            raise e
        elif e.response['Error']['Code'] == 'DecryptionFailureException':
            print("Error getting token: " + e.response['Error']['Code'])
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            print("Error getting token: " + e.response['Error']['Code'])
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            print("Error getting token: " + e.response['Error']['Code'])
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            print("Error getting token: " + e.response['Error']['Code'])
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("Error getting token: " + e.response['Error']['Code'])
            raise e
    else:
        if 'SecretString' in get_secret_value_response:
            return json.loads(get_secret_value_response['SecretString'])['harvest_token']
        else:
        
            print("Error getting token: SecretString property not present")

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

def isThereDuplicateEntries (sourceEntry, destinationEntries):

    try:
        for entry in destinationEntries:
            if (
                sourceEntry['spent_date'] == entry['spent_date'] and
                sourceEntry['notes'] == entry['notes']      and 
                sourceEntry['hours'] == entry['hours']
               ):
                return True

    except Exception as e:

        print("Error in checking duplicate destination entries! - "+ str(e))

    return False

def isThereAnySourceEntry (destinationEntry, sourceEntries):

    try:
        for entry in sourceEntries:
            if (
                destinationEntry['spent_date'] == entry['spent_date'] and
                destinationEntry['notes'] == entry['notes']      and 
                destinationEntry['hours'] == entry['hours']
               ):
                return True

    except Exception as e:

        print("Error in checking existence of source entries! - "+ str(e))

    return False

def lambda_handler(event, context):

    source_harvest_id = 988127
    destination_harvest_id = 1075936
    token = get_token()
    start = (datetime.today() - timedelta(days=3)).strftime("%Y-%m-%d") # Format yyyy-mm-dd
    end =  (datetime.today()).strftime("%Y-%m-%d") # Format yyyy-mm-dd

    print("Syncing from: " + start + ", to: " + end)

    try:
        with open(os.getcwd()+"/mapping.json") as f:

            mapping = json.loads(f.read())
            for user in mapping['users']:
        
                source_url = "https://api.harvestapp.com/v2/time_entries" + "?from=" + start + "&to=" + end + "&user_id=" + str(user['source_user_id'])
                destination_url = "https://api.harvestapp.com/v2/time_entries" + "?from=" + start + "&to=" + end + "&user_id=" + str(user['destination_user_id'])
                headers_source = {
                    "User-Agent": "Harvest Sync App",
                    "Authorization": "Bearer " + str(token),
                    "Harvest-Account-ID": source_harvest_id
                }
                headers_destination = {
                    "User-Agent": "Harvest Sync App",
                    "Authorization": "Bearer " + str(token),
                    "Harvest-Account-ID": destination_harvest_id,
                    "Content-Type": "application/json; charset=utf-8"
                }

                print("Fetching from Source Harvest...")

                get_request_source = urllib.request.Request(url=source_url, headers=headers_source)
                get_response_source = urllib.request.urlopen(get_request_source, timeout=5)

                get_request_destination = urllib.request.Request(url=destination_url, headers=headers_destination)
                get_response_destination = urllib.request.urlopen(get_request_destination, timeout=5)

                if get_response_source.getcode() == 200:

                    print("Sending entries to Destination Harvest...")

                    response_source = get_response_source.read().decode("utf-8")
                    jsonResponse_source = json.loads(response_source)

                    response_destination = get_response_destination.read().decode("utf-8")
                    jsonResponse_destination = json.loads(response_destination)

                    count = 0
                    print( "Items:" + str(len(jsonResponse_source['time_entries'])))

                    for entry in jsonResponse_source['time_entries']:

                        count = count+1
                        
                        try:
                            
                            destination_project_id = getDestinationProjectId(entry['project']['id'], mapping['projects'])
                            destination_task_id = getDestinationTaskId(entry['project']['id'], entry['task']['id'], mapping['projects'])

                            if destination_project_id and destination_task_id is not None:

                                #payload = json.dumps({"project_id":destination_project_id,"task_id":destination_task_id,"spent_date":entry['spent_date'],"hours":entry['hours'],"notes": entry['notes']})
                                payload = json.dumps({"project_id":destination_project_id,"task_id":destination_task_id,"spent_date":entry['spent_date'],"hours":entry['hours'],"notes": entry['notes'], "user_id": entry['user']['id']})
                                payload_bytes = payload.encode('utf-8')

                                if not isThereDuplicateEntries(entry, jsonResponse_destination['time_entries']):

                                    post_request = urllib.request.Request(url=destination_url, headers=headers_destination, method="POST", data=payload_bytes)
                                    post_response = urllib.request.urlopen(post_request, timeout=5)

                        except Exception as e:

                            print("Oops! - Error interating source entries: "+ str(e))

                    print("Removing entries deleted or edited in source Harvest...")

                    for entry in jsonResponse_destination['time_entries']:

                        try:
                            if not isThereAnySourceEntry(entry, jsonResponse_source['time_entries']):

                                url = "https://api.harvestapp.com/v2/time_entries/" + str(entry['id'])
                                delete_request_destination = urllib.request.Request(url=url, headers=headers_destination, method="DELETE")
                                delete_response_destination = urllib.request.urlopen(delete_request_destination, timeout=5)

                                if delete_response_destination.getcode() != 200:

                                    print ("Deleting eroneous entry failed - " + str(delete_response_destination.getcode()))

                        except Exception as e:

                            print("Oops! - Error deleting eroneous entries from destination Harvest: "+ str(e))

                    print("Done!")

                else:
                    print ("Retreiving source time entries failed - " + str(get_response_source.getcode()))
        f.close()

    except Exception as e:

        print("Oops! - "+ str(e))

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
