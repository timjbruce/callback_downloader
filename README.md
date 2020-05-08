# Downloader

This project uses a Step Function to manage the response to a callback URL from a provider. 

## Pre-requisites



## Setup

1. Clone this project to a local or cloud device.  The device should either have an AWS role attached or use an AWS credential that gives admin privileges from a command line.  I personally recommend a Cloud 9 instance with a admin role attached to it.
2. Install AWS SAM onto the device.  A guide can be found [here](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
3. Create a VPC with at least a single public subnet. A guide can be found [here](https://docs.aws.amazon.com/batch/latest/userguide/create-public-private-vpc.html)
4. Attach an Internet Gateway to the VPC. A guide can be found [here](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html)
5. Build the SAM template (template.yaml) using the command `sam build` in the directory with the template.
6. Deploy the SAM template (template.yaml) that is included using the command `sam deploy guided`


## Create an AWS Batch Compute Environment

