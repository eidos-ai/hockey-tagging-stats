# hockey-tagging-stats

Script to export the collections tracks_to_tag and sub_dataset from MongoDB to BigQuery.

## Python packages

Install the required Python packages by executing the following command in your terminal:

```
pip install -r requirements.txt
``` 

## Configuration

Before running the script, you need to modify the configuration information in the 'config.ini' and '.env' files. This consists in providing the necessary details for MongoDB and proivde the path of your google app credentials json file. 

## Run

Once you have completed the setup and configuration, you can start the export process using the following commands:
```
cd src
```
```
python export_to_bigquery.py
```