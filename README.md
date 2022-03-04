# Harvest-Sync

## What does this do?

This is a python script that when supplied with the required options will sync Harvest time entries from one Harvest account to another. At the moment hard coded to sync from Mavericks to Witted.

## How do I do it?

You will need Python 3.* 

Install required packages:
`pip3 install -r requirements.txt`

Create a `mapping.json` file in the same directory as the `synchronize.py` script. The mapping file must follow the same format as the example here. 
Simply run the script with the required parameters

Get yourself a Harvest Personal Access Token from [here](https://id.getharvest.com/developers)

Run the script from within the harvest-sync folder, for example like so:
`./synchronize.py --source $HARVEST_SOURCE_ACCOUNT_ID --destination $HARVEST_DESTINATION_ACCOUNT_ID --token $YOUR_HARVEST_PAT --start 2022-03-01 --end 2022-03-02`

## Caveats

The script is not yet indepotency safe, i.e if you run it twice, it will create the entries twice. Duplicate alert!


## TODO 
- Mapping json schema and validation.
- Implement Indepotency (meaning finish the duplication check function
- Suggestions? Hit me up on Slack @alex
