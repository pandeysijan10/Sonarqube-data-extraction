# Sonarqube-data-extraction
**Data extraction from TUT Sonarqube 6.3**

The program can extract projects individually or all of them in batch. 

**Total number of projects in TUT sonarqube 6.3:** 170

**Types of data for each project:** issues.csv, measures.csv

Each project has these files in a separate folder.

**Fields in ISSUES csv data of each project:**

"creationDate", "updateDate", "closeDate", "type", "rule", "component", 
"severity", "project","startLine", "endLine", "resolution", "status", 
"message", "effort", "debt", "author", "key"

Here "project" means project key, "key" means issue key.

**Issues data for different projects:**

For the projects with <= 10K issues, all of the issues are extracted in
acsending order by creation date.

For the projects with > 10K issues, latest 10K issues by creation date are 
extracted and added to csv in descending order by creation date. This is done
because sonarqube issues API has a limit of 10K results.

**Fields in MEASURES csv data of each project:**

'projectName', 'sonarVersion', 'measure-date', '{all the active metrics for the 
project as separate headers}'

Here 'projectName' means project key.

All measures are extracted for all projects.





