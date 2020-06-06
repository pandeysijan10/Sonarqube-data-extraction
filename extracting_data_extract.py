"""
Author: Sijan Pandey
Email: sijan.pandey@tuni.fi
Description: A program to extract measures and issues of projects from a sonarqube instance.
The measures and issues data is saved in separate csv files for each project.
"""

import json
import csv
import requests
import pandas as pd
import os
import urllib.parse

# headers for issues csv file fields
ISSUES_HEADERS = ["creationDate", "updateDate", "closeDate", "type", "rule", "component", "severity", "project",
                  "startLine", "endLine", "resolution", "status", "message", "effort", "debt", "author", "key"]

SONAR_VERSION = 'sonar63'
START_DATE = '1900-01-01T01:01:01+0100'

# max issues that can be obtained
MAX_REQUEST = 10000


def get_issues(project_key):
    # gets issues for the particular project and writes to a csv file

    issues_url_response = requests.get(
        "http://" + SONAR_VERSION + ".rd.tut.fi//api/issues/search?componentKeys="
        + project_key + "&s=CREATION_DATE&statuses=OPEN,CLOSED&createdAfter="
        + urllib.parse.quote(START_DATE) + "&ps=1&p=1")

    if issues_url_response.status_code == 200:
        total_issues = int(issues_url_response.json()['total'])
        less_than = False

        if total_issues <= MAX_REQUEST:
            less_than = True

        csv_output = "issues.csv"
        with open(csv_output, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=';')
            csv_writer.writerow(ISSUES_HEADERS)
        csv_file.close()

        issues_to_csv(csv_output, project_key, total_issues, less_than)


def issues_to_csv(csv_output, project_key, total_issues, less_than):
    # goes through all the pages of issues and gets all the required fields of data
    i = 1
    while i <= total_issues and i <= 10000:
        if less_than:
            # if total issues is less than 10000 get all of them
            issues_url_response = requests.get(
                "http://" + SONAR_VERSION + ".rd.tut.fi//api/issues/search?componentKeys="
                + project_key +
                "&s=CREATION_DATE&statuses=OPEN,CLOSED&createdAfter="
                + urllib.parse.quote(START_DATE) + "&ps=1&p="
                + str(i))

        else:
            # if total issues > 10000 get only the latest 10000 issues
            issues_url_response = requests.get(
                "http://" + SONAR_VERSION + ".rd.tut.fi//api/issues/search?componentKeys="
                + project_key +
                "&s=CREATION_DATE&statuses=OPEN,CLOSED&createdAfter="
                + urllib.parse.quote(START_DATE) + "&ps=1&p="
                + str(i) + "&asc=false&branch=master")

        i = i + 1
        issues_response_list = issues_url_response.json()['issues']
        extracted_issue_list = []
        for iss in ISSUES_HEADERS:
            if iss in issues_response_list[0].keys():
                extracted_issue_list.append(issues_response_list[0][iss])
            else:
                if 'textRange' in issues_response_list[0].keys():
                    if (iss == 'startLine' or iss == 'endLine' and
                            iss in issues_response_list[0]['textRange'].keys()):
                        extracted_issue_list.append(
                            issues_response_list[0]['textRange'][iss])
                    else:
                        extracted_issue_list.append('')
                else:
                    extracted_issue_list.append('')
        with open(csv_output, 'a', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=';')
            csv_writer.writerow(extracted_issue_list)
    if total_issues != 0:
        csv_file.close()


def get_all_metrics():
    # Didn't bother to check the total number of metrics for the sonarqube
    # instance. For this, it is 238 and it is <500(permitted value) so directly
    # included in ps
    metrics_url_response = requests.get(
        "http://" + SONAR_VERSION + ".rd.tut.fi/api/metrics/search?ps=238")
    metrics_data = metrics_url_response.json()['metrics']
    all_metrics_key = []
    for met in metrics_data:
        all_metrics_key.append(met['key'])
    return all_metrics_key


def get_measures(all_metrics_key, project_key):
    # gets all measures for all active metrics for a project and creates
    # a csv file with the data
    measure_headers = ['projectName', 'sonarVersion', 'measure-date']

    active_metrics = get_active_metrics(all_metrics_key, project_key)
    # adding active metrics name to list of headers of measures_csv file
    for i in range(0, len(active_metrics)):
        measure_headers.append(active_metrics[i])
    csv_output = "measures.csv"

    # getting total number of pages
    req_json = requests.get(
        "http://" + SONAR_VERSION +
        ".rd.tut.fi/api/measures/search_history?p=1&ps=1000&component="
        + project_key + "&metrics=" + active_metrics[0])
    total_measures = req_json.json()['paging']['total']
    iterations = (total_measures // 1000) + 1
    i = 1
    date_list = []

    # getting all the measures dates available for all the metrics
    while i <= iterations:
        req_json = requests.get(
            "http://" + SONAR_VERSION +
            ".rd.tut.fi/api/measures/search_history?p="
            + str(i) + "&ps=1000&component=" + project_key + "&metrics=" +
            active_metrics[0])
        history_list = req_json.json()['measures'][0]['history']
        for k in range(0, len(history_list)):
            date_list.append(
                req_json.json()['measures'][0]['history'][k]['date'])
        i = i + 1

    # creating columns for the measures csv file with length that of total
    # number of measure dates
    # Note: first active metric in alphabetical orders of active metrics has
    # maximum amount of measurement dates. So, date list is created from first
    # active metrics
    proj_list = [project_key] * (len(date_list))
    sonar_version = [SONAR_VERSION] * len(date_list)

    # adding project key and sonar version column fields to csv file using
    # pandas
    pd.DataFrame({measure_headers[0]: proj_list,
                  measure_headers[1]: sonar_version,
                  measure_headers[2]: date_list}).to_csv(csv_output,
                                                         index=False, sep=';')

    # getting measure value for each date available for all the metrics and
    # adding to csv, if all dates for that particular metric not available
    # then '' value is given for the corresponding date.
    # Note: first active metric in alphabetical orders of active metrics has
    # maximum amount of measurement dates. So, date list is created from first
    # active metrics
    col_list = [''] * (len(date_list))
    # all data of a metric is taken at a time
    for j in range(0, len(active_metrics)):
        col_list.clear()
        col_list = [''] * (len(date_list))
        i = 1
        # goes through every page of the data for the particular metric
        while i <= iterations:
            req_json = requests.get(
                "http://" + SONAR_VERSION +
                ".rd.tut.fi/api/measures/search_history?p="
                + str(i) + "&ps=1000&component=" + project_key + "&metrics=" +
                active_metrics[j])
            history_list = req_json.json()['measures'][0]['history']

            # date and corresponding value are data for each active metric
            for k in range(0, len(history_list)):
                ind = date_list.index(history_list[k]['date'])
                col_list[ind] = history_list[k]['value']
            i = i + 1

        # after getting all the values for individual metric for all the dates,
        # data is added as new column to measures_csv
        col_dat = pd.read_csv(csv_output, sep=';')
        col_dat[measure_headers[j + 3]] = col_list
        col_dat.to_csv(csv_output, index=False, sep=';')


def get_active_metrics(all_metrics_key, project_key):
    # returns all metrics that are active for the particular project in a list
    active_metrics = []
    for metric_key in all_metrics_key:
        measures_url_response = requests.get(
            "http://" + SONAR_VERSION +
            ".rd.tut.fi/api/measures/component?componentKey="
            + project_key + "&metricKeys=" + metric_key)
        if len(measures_url_response.json()['component']['measures']) != 0:
            active_metrics.append(
                measures_url_response.json()['component']['measures'][0]['metric'])
    active_metrics = sorted(active_metrics)
    return active_metrics


def get_projects():
    # gets all the project in the sonarqube instance and the project keys in a
    # dict, also returns the total number of projects
    project_req = requests.get(
        "http://" + SONAR_VERSION +
        ".rd.tut.fi//api/components/search?qualifiers=TRK&ps=500&p=1")
    projects = {}
    for comp in project_req.json()['components']:
        projects[comp['key']] = comp['name']
    total = project_req.json()['paging']['total']
    return projects, int(total)


def main():
    dir = os.path.join("sonarqube_projects")
    if not os.path.exists(dir):
        os.mkdir(dir)

    projects, total_proj = get_projects()

    num = 1
    for key in projects.keys():
        print(str(num) + ' ' + projects[key])
        num = num + 1
    user_inp = input(
        "Type project number to choose one project or type 'all' in lowercase "
        "letters to extract all projects: ")

    old_dir = os.getcwd()
    if user_inp == 'all':
        for project_key in projects.keys():
            os.chdir(old_dir)
            dir = os.path.join("sonarqube_projects", projects[project_key])
            if not os.path.exists(dir):
                os.mkdir(dir)
            os.chdir(dir)

            all_metrics_key = get_all_metrics()

            print('Extracting issues for ' + projects[project_key])
            get_issues(project_key)
            print('Completed extracting issues for ' + projects[project_key])

            print('Extracting measures for ' + projects[project_key])
            get_measures(all_metrics_key, project_key)
            print('Completed extracting measures for ' + projects[project_key])

    elif int(user_inp) <= 170:
        num = 1
        for project_key in projects.keys():
            if num == int(user_inp):
                os.chdir(old_dir)
                dir = os.path.join("sonarqube_projects", projects[project_key])
                if not os.path.exists(dir):
                    os.mkdir(dir)
                os.chdir(dir)

                all_metrics_key = get_all_metrics()

                print('Extracting issues for ' + projects[project_key])
                get_issues(project_key)
                print('Completed extracting issues for ' +
                      projects[project_key])

                print('Extracting measures for ' + projects[project_key])
                get_measures(all_metrics_key, project_key)
                print('Completed extracting measures for ' +
                      projects[project_key])

            num = num + 1

    else:
        print('Invalid input')
        return 1

    return 0


main()
