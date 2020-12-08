[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) 
# Agent Module For Google Cloud Platform

## Quick Start Guide
Download the source code:
```
git clone https://github.com/X-I-A/agent-gcp
cd agent-gcp
```
Please using Google Cloud Console or have Google Cloud SDK installed
1. `make config` Setting project id, cloud run region and cloud run platform
2. `make init` **Only Once per project** Activation of API, creation of service account with roles
3. `make build` Build and upload Cloud Run Images
4. `make deploy` Deploy Cloud Run Image by using the last built image

Now you can create topics by using the following command
* `make create-topic`
