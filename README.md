# Downloader

This project uses a Step Function to manage the response to a callback URL from a provider. 

## Pre-requisites
1. Install Docker.  I am testing with Docker 19.03.6-ce for this project.
2. Install the AWS cli.  Instructions can be found (here)[https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html]
3. Install AWS SAM.  Instructions can be found (here)[https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html]
4. Make sure git is installed.
5. It is recommended to run these from a device where you have privileges to use the above software and that has privileges to administer an AWS account.  I recommend Cloud9 with an Admin role attached.

## Setup

1. Clone this project to your device using git.
2. Create a VPC with at least a single public subnet. A guide can be found [here](https://docs.aws.amazon.com/batch/latest/userguide/create-public-private-vpc.html).  If you choose, you can use the Default VPC in your account and skip this step.
4. Attach an Internet Gateway to the VPC. A guide can be found [here](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html)
5. Build the SAM template (template.yaml) using the command `sam build` in the directory with the template.
6. Run the SAM template through SAM (template.yaml) that is included using the command `sam deploy --guided`.  Use the following responses for the prompts:
   a.  Stack Name: downloader
   b.  AWS Region: <aws region you are working in>
   c.  Confirm changes before deploy: Y
   d.  Allow SAM CLI IAM role creation: Y
   e.  Save arguments to samconfig.toml: Y
**Note, after the first run, deploy using just 'sam deploy --capabilities CAPABILITY_NAMED_IAM'**

Copy the outputs of the SAM deploy for future reference and use.


## Create the Container for the Batch Download Job
AWS Batch uses ECR and Containers to run.  The Batch download job will be able to handle larger file sizes than Lambda currently, due ot /tmp sizing of Lambda.  This part of the process will create the container image and upload it to ECR, which is used by AWS Batch to run jobs.

1. Navigate to the ECR service in AWS Console
2. Click Getting Started
3. Create a new repository named `downloader`

Go back to the console for the workstation you have cloned the project to for the next set of steps.
1. Navigate to the callback_downloader/DockerImages/Downloader directory
2. Use the command `docker build -t downloader:1.0 .` to build the container
3. Tag this container to an ECR container using the command `docker tag downloader:1.0 <accountnumber>.dkr.ecr.<yourregion.amazonaws.com/downloader:latest`, replacing <accountnumber> with your account number and <yourregion> with your deploy target region.
4. Login to your ECR with the command `aws ecr get-login-password --region <yourregion> | docker login --username AWS --password-stdin <accountnumber>.dkr.ecr.<yourregion>.amazonaws.com`, replacing <accountnumber> with your account number and <yourregion> with your deploy target region.
5. Push the container to ECR using the command `docker push <accountnumber>.dkr.ecr.<region>.amazonaws.com/downloader:latest`, replacing <accountnumber> with your account number and <yourregion> with your deploy target region.

Return back to the console for ECR and copy the image URI for the Downloader repository name.

## Create an AWS Batch Compute Environment
AWS Batch requires a Compute Environment, Job Queue, and Job Definition to be able to execute jobs.  This part of the process will set all of these up.  This is a pre-requisite for the Step Function.

1. Go to AWS Batch in the AWS Console.
2. Click Get Started.  This will start the Job Definition steps of the process.  If you have used Batch before, you may be at a menu.  Click 
3. Enter the following parameters:
   Using EC2: Selected
   Job Definition: Create New Job Definition
   Job Definition Name: <from SAM outputs: DownloaderJobIAMRole - Role for Downloader Job>
   Container Image: <the copied value for the Downloader repository name>
   Command: python3 lambda_function.py Ref::URI
   vCPUs: 2
   MiB: 512
   Job Attempts: 1
   Add a Parameter by clicking the + sign in the Parameters section
   Key: URI, Value: Test
   Click Next

We are now setting up a Compute Environment and a Job Queue for the Job to run in.
1. Enter the following parameters:
   Compute Environment Name: Downloader
   Service Role: <from SAM output: BatchIAMRole - Role for Downloader Job>
   EC2 Instance Role: <from SAM output: InstanceIAMProfile - Instance Profile for Downloader Job>
   Provisioning Model: On Demand
   Allowed Instance Types: Optimal
   Minimum vCPUs: 2
   Desired vCPUs: 2
   Maximum vCPUs: 12
   VPC ID: Select your VPC to use (must have IGW access with a route for 0.0.0.0/0 to the IGW)
   Subnets:  Select any you want to use
   Security Group: select a default
   Job Queue Name: Downloader
2. Click Create 

## Setup the Step Function 
1. Navigate to Step Functions in the AWS Console
2. Click on State Machines in the Menu
3. Click Create State Machine
4. 

CallbackUrl on downloader