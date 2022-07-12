# Snowflake External Functions

This repo contains source code for all functions that are deployed to AWS Lambda and then connected to a [Snowflake external function](https://docs.snowflake.com/en/sql-reference/external-functions-introduction.html).

As this serverless deployment uses Lambda's support for Docker containers, functions can be coded in any language as long as they can be dockerized in a container running the [AWS Lambda runtime](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html).

This project has been generated using the `aws-python-docker` template from the [Serverless framework](https://www.serverless.com/).

For detailed instructions, please refer to the [documentation](https://www.serverless.com/framework/docs/providers/aws/).

## Installation

There are several ways to [install](https://www.serverless.com/framework/docs/getting-started) `serverless` but the easiest is by using `npm` by running this command:

```{bash}
npm install -g serverless
```

Next you'll need to configure serverless with your [AWS credentials](https://www.serverless.com/framework/docs/providers/aws/guide/credentials/) for deploying to AWS.

If you have an existing [AWS credentials profile](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html) set up, you can run the deploy command and add the `--profile my-aws-creds-profile-name` option.

Otherwise, you can configure you credentials with this command:

```{bash}
serverless config credentials \
  --provider aws \
  --key <AWS-ACCESS-KEY> \
  --secret <AWS-SECRET-KEY>
```

## Deployment instructions

> **Requirements**: Docker. In order to build images locally and push them to ECR, you need to have Docker installed on your local machine. Please refer to [official documentation](https://docs.docker.com/get-docker/).

In order to deploy your service, run the following command

```{bash}
serverless deploy
```

## Test your service

After successful deployment, you can test your service remotely by using the following command:

```{bash}
sls invoke --function my-function-name
```
