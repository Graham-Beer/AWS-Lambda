<h1> AWS Lambda to Send EC2 and RDS startup alerts to Microsoft Teams via a webhook <h1>


Required steps:
1. Create two **SNS topics**, one each for EC2 and RDS.
2. Create **Lambda**:
   1. IAM role will need *AWSLambdaBasicExecutionRole, AmazonEC2ReadOnlyAccess and AmazonRDSReadOnlyAccess*
   2. Set **Environment variables**
      1. **HookUrl** = The webhook address
      2. **required_tags** = Tags that are required for display. In the following format for the value:	
         'Name', 'Owner', 'Backup', 'Application'
   3. Add **Lambda MS Teams.py** as the main Lambda function. Add a second python file called **accounts.py** for account information.
3. Enable **CloudTrail** for Lambda api's, selecting the Lambda just created. Create an S3 bucket on creation of CloudTrail setup.
4. Add two **CloudWatch Event Rules** for RDS and EC2. Use the two Event pattern json files to create. Under Targets, use the drop down to    select required SNS. Make sure the configure input is set to "Matched event".

**NOTE: All Lambda's in Python 3.8**
