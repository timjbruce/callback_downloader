# Downloader

This project uses an AWS Step Function to manage the response to a callback URL from a provider. <br>

This Step Function is a State Machine that allows an organization to create a unique callback URL for a project and wait for a callback.  When the callback URL is accessed by the third party, a AWS Lambda function will signal the State Machine to continue.  Upon continuing, the State Machine will download a list of files from a pre-configured location using a Lambda function and then download the files using AWS Batch.<br>

For those unfamiliar, a callback is used when processing is performed by a third party which could take an extended period of time.  This type of process allows you to automatically respond to åthe callback and then continue processing.<br>
![Overview of Callback Process](https://raw.githubusercontent.com/timjbruce/callback_downloader/master/images/callbackprocess.png)

The State Machine is the feature that is managing the process on your side and taking action upon the signal from the third party.  In this case, the State Machine is simply 3 steps:
1. Create a UUID and Callback token, given a projectid, store these values in Amazon DynamoDB, and wait.
2. Upon signal to continue, download a file list using a mock endpoint created in this project and store the records in DynamoDB
3. Download the list of files using AWS Batch 
![Overview of Step Function](https://raw.githubusercontent.com/timjbruce/callback_downloader/master/images/stepfunction.png)

<br>
AWS Batch is used, currently, due to space limitations with AWS Lambda.  Future versions of this will replace the file list storing in DynamoDB with Amazon SQS and the AWS Batch downloader with AWS Lambda.  This will allow for multiple files to be downloaded at the same time without requiring knowledge of thread-safe development or the concern of utilization of all vCPUs in an AWS Batch environment.<br>

## Pre-requisites
1. Install Docker.  I am testing with Docker 19.03.6-ce for this project.
2. Install the AWS cli.  Instructions can be found (here)[https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html]
3. Install AWS SAM.  Instructions can be found (here)[https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html]
4. Install git.  Instructions can be found (here)[https://git-scm.com/book/en/v2/Getting-Started-Installing-Git]
5. It is recommended to run these from a device where you have privileges to use the above software and that has privileges to administer an AWS account.  I recommend Cloud9 with an Admin role attached.

## Setup

1. Clone this project to your device using git.
2. Create a VPC with at least a single public subnet. A guide can be found [here](https://docs.aws.amazon.com/batch/latest/userguide/create-public-private-vpc.html).  If you choose, you can use the Default VPC in your account and skip this step.
4. Attach an Internet Gateway to the VPC. A guide can be found [here](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html)
5. Build the SAM template (template.yaml) using the command `sam build` in the directory with the template.
6. Run the SAM template through SAM (template.yaml) that is included using the command `sam deploy --guided`.  Use the following responses for the prompts:
   - Stack Name: downloader
   - AWS Region: <aws region you are working in>
   - Confirm changes before deploy: Y
   - Allow SAM CLI IAM role creation: Y
   - Save arguments to samconfig.toml: Y

<br>
**Note, after the first run, deploy using just 'sam deploy --capabilities CAPABILITY_NAMED_IAM'**

Copy the outputs of the SAM deploy for future reference and use.


## Create the Container for the Batch Download Job
AWS Batch uses ECR and Containers to run.  The Batch download job will be able to handle larger file sizes than Lambda currently, due to /tmp sizing of Lambda.  This part of the process will create the container image and upload it to ECR, which is used by AWS Batch to run jobs.

1. Navigate to the ECR service in AWS Console
2. Click Getting Started
3. Create a new repository named `downloader`

<br>
Go back to the console/command line for the workstation you have cloned the project to for the next set of steps.
<br>

<br>

4. Navigate to the callback_downloader/DockerImages/Downloader directory
5. Modify the lambda_function.py file (lines 8 - 10) and save the file.
   - Line 8: Change <Region> to the AWS Region you deployed the SAM template to
   - Line 9: Change <DynamoDBFilesTable> to the output value for DynamoDBFilesTable - DynamoDB Table for File Downloading
   - Line 10: Change <S3Bucket> to the output value for S3Bucket - S3 Bucket for Copy of Files 
6. Use the command `docker build -t downloader:1.0 .` to build the container
7. Tag this container to an ECR container using the command `docker tag downloader:1.0 <accountnumber>.dkr.ecr.<region>.amazonaws.com/downloader:latest`, replacing <accountnumber> with your account number and <region> with your deploy target region.
8. Login to your ECR with the command `aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <accountnumber>.dkr.ecr.<region>.amazonaws.com`, replacing <accountnumber> with your account number and <region> with your deploy target region.
9. Push the container to ECR using the command `docker push <accountnumber>.dkr.ecr.<region>.amazonaws.com/downloader:latest`, replacing <accountnumber> with your account number and <region> with your deploy target region.

<br>
Return back to the console for ECR and copy the image URI for the Downloader repository.
<br>

## Create an AWS Batch Compute Environment
AWS Batch requires a Compute Environment, Job Queue, and Job Definition to be able to execute jobs.  This part of the process will set all of these up.  This is a pre-requisite for the Step Function.
<br>
1. Go to AWS Batch in the AWS Console.
2. Click Get Started.  This will start the Job Definition steps of the process.  If you have used Batch before, you may be at a menu.  Please follow Alternate Steps for Setting Up AWS Batch below. 
3. Enter the following parameters:
   - Using EC2: Selected
   - Job Definition: Create New Job Definition
   - Job Definition Name: Downloader
   - Job Role: <from SAM outputs: DownloaderJobIAMRole - Role for Downloader Job>
   - Container Image: <the copied value for the Downloader repository name>
   - Command: python3 lambda_function.py Ref::URI
   - vCPUs: 2
   - MiB: 512
   - Job Attempts: 1
   - Add a Parameter by clicking the + sign in the Parameters section
      - Key: URI, Value: Test
   - Click Next

<br>
We are now setting up a Compute Environment and a Job Queue for the Job to run in.
<br>

4. Enter the following parameters:
   - Compute Environment Name: Downloader
   - Service Role: <BatchIAMRole - Role for Batch Service>
   - EC2 Instance Role: <from SAM output: InstanceIAMProfile - Instance Profile for Downloader Job>
   - Provisioning Model: On Demand
   - Allowed Instance Types: Optimal
   - Minimum vCPUs: 2
   - Desired vCPUs: 2
   - Maximum vCPUs: 12
   - VPC ID: Select your VPC to use (must have IGW access with a route for 0.0.0.0/0 to the IGW)
   - Subnets:  Select any you want to use.  You must have at least 1.
   - Security Group: select a default security group
   - Job Queue Name: Downloader

<br>
5. Click Create 

<br>
It will take a few moments for your Batch Compute Environment to build.  Please wait for it to be completed before starting on the next step.
<br>
Once the Environment is Built, perform the following steps:
5. Click Job Definitions in the menu on the left navigation bar
6. Click the `downloader` Job Definition
7. Click `Revision 1`
8. Copy the Job Definition Arn for future use.  It should look like arn:aws:batch:<region>:<account>:job-definition/downloader:1
9. Click on Job Queues in the menu on the left navigation bar
10. Click the `downloader` Queue Name
11. Copy the Queue Arn for future use.  It should look like  arn:aws:batch:<region>:<account>:job-queue/Downloader 

## Alternate Steps for Setting Up AWS Batch 

If you could not complete the previous step via the wizard due to having an existing AWS Batch Environment, follow these steps.  If you were successful in completing the prior steps, please move on to Setup the Step Function.
1. Click on Compute Environment in the Left Hand Navigation
2. Click Create Environment
3. Choose the following options:
    - Managed Environment
    - Name: Downloader
    - Service Role: <BatchIAMRole - Role for Batch Service>
    - EC2 Instance Role: <from SAM output: InstanceIAMProfile - Instance Profile for Downloader Job>
    - Provisioning Model: On Demand
    - Allowed Instance Types: Optimal
    - Minimum vCPUs: 2
    - Desired vCPUs: 2
    - Maximum vCPUs: 12
    - VPC ID: Select your VPC to use (must have IGW access with a route for 0.0.0.0/0 to the IGW)
    - Subnets:  Select any you want to use.  You must have at least 1.
    - Security Group: select a default security group
4. Click Create to create your Compute Environment
5. Click on Job queues on the Left Hand Navigation
6. Click Create Queue
7. Enter the following values:
    - Queue Name: downloader
    - Priority 1
    - Enable Job Queue: Checked
    - Select the Downloader Compute Environment to link it to this queue
8. Click Create Job Queue
9. Click the Queue Name and then copy the queue Arn for later use.
10. Click on Job Definitions on the Left Hand Navigation
11. Click Create
12. Enter the following values:
    - Job Definition Name: Downloader
    - Job Attempts: 1
    - Click on Add Parameter to Add a Key of "URI" and a value of "Test"
    - Job Role: <from SAM outputs: DownloaderJobIAMRole - Role for Downloader Job>
    - Container Image: <the copied value for the Downloader repository name>
    - Command: python3 lambda_function.py Ref::URI
    - vCPUs: 2
    - MiB: 512
13. Click Create Job Definition
14. Click the Job Definition Name
15. Click the Revision Number (should be 1 unless you have a previous Job with the same name)
16. Copy the Job Definition Arn for later use


## Setup the Step Function 
Before we setup the Step Function in the AWS Console, we are going to edit the file to update it for the functions that have been deployed in your account.  Please return to the console/command line for the workstation you have cloned the project to for the next set of steps.

1. Navigate to the StepFunction folder for your project
2. Edit the File `stepfunction.json`
   - Line 12: Replace <WaiterFunction - Lambda function to wait for callback > with the value from the SAM template outputs
   - Line 27: Replace <FileListDownloader - Lambda function to download file list> with the value from the SAM template outputs
   - Line 41: Replace <JobDefinitionArnyn> with the Job Definition Arn you copied above
   - Line 43: Replace <JobQueueArn> with the Job Queue Arn you copied above
3. Save the file and copy its contents.

<br>
Return to the AWS Console for the next set of steps.
<br>

4. Navigate to Step Functions in the AWS Console
5. Click on State Machines in the Left Hand Menu
6. Click Create State Machine
7. Choose the following options.
   - Author with Code Snippets
   - Type: Standard
8. Delete the JSON content in Definition
9. Paste in your updated Step Function that was modified in the steps above.
10. Click Next
11. Enter the following values
   - Name: Downloader
   - Permissions: Choose an existing role
   - Role: Choose the Role for <StepFunctionsIAMRole - Role for Step Function> from the SAM output
   - Logging Level: Off
12. Click Create State Machine

<br>
Logging requires additional IAM configuration to allow the Step Function Role to write to CloudWatch Logs.  You can find information about the changes required [here](https://docs.aws.amazon.com/step-functions/latest/dg/cw-logs.html).
<br>

## Running the State Machine

The State Machine in this example is kicked off using the AWS Step Functions Console.<br>

1. Navigate to AWS Step Functions
2. Click on State Machines
3. Click Downloader to navigate to the Details page for the State Machine.
4. Click Start Execution

<br>
At this point, you wiill see a screen with an Execution Name and Input section.  The Execution Name is a generated from the console and should be unique for the purposes of this State Machine.  The Execution Name will also act as the callback URI that is appended to the <CallbackURL - URL for Callback> that was generated in the SAM template.  An example is:
<br>
   >>https://12354346346.execute-api.us-east-2.amazonaws.com/dev/callbacka/eba43abb-fd2b-da4f-03d4-43a8b26b4eee
<br>

5. In the Input Section, paste in `{ 'projectid': '1234567'}` .  The projectid value does not need to be unique for this project.
6. Copy the value for the Execution Name for performing the callback.

<br>
At this point, your process should look similar to the below image.  The process will stay like this until a callback is received.  You may start additional State Machines and have a number of them waiting for callback.

![Awaiting Callback](https://raw.githubusercontent.com/timjbruce/callback_downloader/master/images/step1.png)

<br>
7. At a console, type in `curl -X POST <CallbackURL - URL for Callback>/<ExecutionName>` and press enter.  Replace the CallbackURL with the value from your SAM outputs and the ExecutionName with one of your Step Function Execution Names.  This will send the signal to Step Functions to continue that execution.

<br>
If you watch close enough, you will see the "WaitForCallback" Step wiill turn Green, to signify it has completed successfully.  The "GetFilesToDownload" step will turn Blue to show it is proceeding.  It may turn Green rather quickly, which is good as that signals success.  In this case, the "DownloadFiles" step will turn Blue to show it is starting.

![Callback Has Occurred](https://raw.githubusercontent.com/timjbruce/callback_downloader/master/images/step2.png)

![Downloading Files](https://raw.githubusercontent.com/timjbruce/callback_downloader/master/images/step3.png)


<br>
After the conclusion of downloading the files, your process should show green for all steps, like below.  Additionally, if you check in your S3 bucket, you will find a set of keys for the Execution Name matching those provided by the Mock API.

![Process Complete](https://raw.githubusercontent.com/timjbruce/callback_downloader/master/images/complete.png)
