import boto3
from botocore.exceptions import NoCredentialsError
from bs4 import BeautifulSoup
from datetime import date, datetime
import dateparser
import json
import os
import re
import requests

from dotenv import load_dotenv
load_dotenv()

S3_ACCESS_KEY = os.environ['S3_ACCESS_KEY']
S3_SECRET_KEY = os.environ['S3_SECRET_KEY']
S3_REPORTS_BUCKET = os.environ['S3_REPORTS_BUCKET']


def get_report_data(report_url):
    html = requests.get(report_url)
    soup = BeautifulSoup(html.text, 'html.parser')

    recap = soup.find('div', {'class': 'recap'})
    children = recap.findChildren('div', recursive=False)

    # define the titles we care about
    titles = [
        'Date', 'Conseil', 'Vagues', 'Vent', 'Plan d\'eau', 'Niveau', 'Conseil'
    ]

    formattedRecap = {}

    for child in children:
        title = child.find('div', {'class': 'top'})

        if title is not None and title.text in titles:
            formattedRecap[title.text] = child.find('div', {
                'class': 'ti'
            }).text

    return formattedRecap


def upload_to_aws(local_file, bucket, s3_file):
    s3 = boto3.client('s3',
                      aws_access_key_id=S3_ACCESS_KEY,
                      aws_secret_access_key=S3_SECRET_KEY)

    try:
        s3.upload_file(local_file, bucket, s3_file)
        print('Upload Successful')
        return True
    except FileNotFoundError:
        print('The file was not found')
        return False
    except NoCredentialsError:
        print('Credentials not available')
        return False


def main():
    # get all links on page
    url = 'https://www.surf-report.com/reports/'

    # get all a elements where link starts with '/reports/' and element title starts with 'Report'
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')
    reports = soup.find_all('a', {
        'href': re.compile('^\/reports\/.*html$'),
        'title': re.compile('^Report')
    })

    reports_data = []
    for report in reports:
        url = 'https://www.surf-report.com' + report['href']
        print('URL: {}'.format(url))

        # get report data
        data = get_report_data(url)

        # format surf-report date into datetime object
        report_date_obj = dateparser.parse(data['Date'], languages=['fr'])

        # only save reports from present day
        if (datetime.today() - report_date_obj).days == 0:
            data['Date'] = report_date_obj.strftime('%Y-%m-%d %H:%M:%S')
            data['url'] = url
            reports_data.append(data)

    # write in files and upload if we have at least 1 report
    if len(reports_data) > 0:
        with open('reports.json', 'w') as outfile:
            json.dump(reports_data, outfile, ensure_ascii=False)

        return upload_to_aws('reports.json', S3_REPORTS_BUCKET,
                             date.today().strftime("%Y-%m-%d") + '.json')


if __name__ == '__main__':
    main()
