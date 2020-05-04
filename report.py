import re
import requests
from bs4 import BeautifulSoup
import json


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
        data = get_report_data(url)
        data['url'] = url
        reports_data.append(data)

    # write in files
    with open('reports.txt', 'a') as file:
        for data in reports_data:
            file.write('{}\n'.format(data))


if __name__ == '__main__':
    main()