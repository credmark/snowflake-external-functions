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

### Using `make`

The [Makefile](./Makefile) has deployment targets configured for both dev and prod environments. `deploy-dev` will deploy the service to the AWS dev account and requires having the `AWS_DEV_PROFILE` environment variable set. This environment variable should have the name of the AWS CLI profile name that points to the AWS dev account. Read the [docs](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html) for more information on setting up named AWS CLI profiles.

### Using `serverless`

> **Requirements**: Docker. In order to build images locally and push them to ECR, you need to have Docker installed on your local machine. Please refer to [official documentation](https://docs.docker.com/get-docker/).

In order to deploy your service, run the following command

```{bash}
serverless deploy --stage <STAGE NAME> --region <AWS REGION> --aws-profile <AWS CLI PROFILE NAME>
```

## Test your service

After successful deployment, you can test your service remotely by using the following command:

```{bash}
sls invoke --function my-function-name
```

## Development

This project is managed with [poetry](https://python-poetry.org/) which is a very useful and modern package and dependency management tool for python. Installation instructions can be found [here](https://python-poetry.org/docs/#installation). Once `poetry` is installed, to install this project locally, run the following:

```{shell}
poetry install
```

This will install all the package dependencies as defined in [pyproject.toml](./pyproject.toml). If you need to add a new package, instead of using `pip` as you normally would you would run the following:

```{shell}
poetry add numpy
```

> *Note: this is the equivalent of running `pip install numpy` but the package dependencies will be added to [pyproject.toml](./pyproject.toml) and any conflicts with other packages will be identified and/or resolved automatically for you.

### Virtual environment

`poetry` will create a separate environment per project. If you want to run the code locally using the packages installed in the project, you need to activate the environment by running:

```{shell}
poetry shell
```

This will activate the environment where all the project dependencies are installed. To exit the environment, just run `exit` in the terminal.

## Adding New Function and Creating New Lambda

Adding a new lambda for deployment via `serverless` is simple. First, you will need to add a new handler to the [handlers.py](./src/handlers.py). You can create modules in separate files but the handler that serves as the entrypoint to your function will need to be in this file.

For AWS Lambda, handlers require the following signature:

```{python}
def my_handler_func(event: dict, context: dict):
    # code
```

Additionally, since these functions are configured with an API gateway to be triggered via API, they must return proper http status and headers, i.e.:

```{python}
return {
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
    "body": json.dumps(some_json_data)
}
```

Finally, you just need to add the new function in [serverless.yml](./serverless.yml) under the "functions" key like so:

```yaml
functions:
  my-handler-func:
    image:
      name: appimage
      command: ["handlers.my_handler_func"]  # Change the command to use the name of the handler defined in handlers.py
    events:
      - http:
          path: /some/api/endpoint/path  # Update the path to reflect the correct protocol and metric being used
          method: POST
```

> *Note: adding the `events` key will create a new API gateway endpoint where the lambda can be triggered. In the case above, this would create a new endpoint with the path `some-url.com/some/api/endpoint/path

## Setting up external function in Snowflake

This serverless function is deployed via a [github workflow](.github/workflows/deploy.yml). However, there are additional resources that must be created in order to allow Snowflake to call this external function. Unfortunately (for now), these resources must be created by hand and cannot be automated with Terraform as there are circular dependencies involved.

[This](https://data.solita.fi/snowflake-external-functions-tutorial-for-aws-lambda/) guide was used to setup the correct IAM and Snowflake resources.

The general steps are:

1. Create an IAM role
2. Navigate to the API gateway of the Lambda function and change the authorization mode in the "Method Request" section of the endpoint to use "AWS_IAM".
3. Copy the ARN of the endpoint
4. Create a resource policy in API gateway using this template:

    ```{json}
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:sts::<ACCOUNT ID>:assumed-role/<CREATED IAM ROLE NAME>/snowflake"
                },
                "Action": "execute-api:Invoke",
                "Resource": "arn:aws:execute-api:<AWS REGION>:<ACCOUNT ID>:<API GATEWAY ID>/*/POST/<API RESOURCE PATH>"
            }
        ]
    }
    ```

5. Navigate to Snowflake and create a new API integration object:

    ```{sql}
    create or replace api integration <INTEGRATION NAME>
    api_provider = aws_api_gateway
    api_aws_role_arn = 'arn:aws:iam::<ACCOUNT ID>:role/<IAM ROLE NAME>'
    enabled = true
    api_allowed_prefixes = ('https://<API GATEWAY ID>.execute-api.<AWS REGION>.amazonaws.com/<API GATEWAY STAGE NAME>/');
    ```

6. Run the following command to grab the values for `API_AWS_IAM_USER_ARN` and `API_AWS_EXTERNAL_ID`:

    ```{sql}
    describe integration <INTEGRATION NAME>;
    ```

7. Go back to AWS and edit the trust relationship policy document of the IAM role created in step 1. Replace the current value of `Statement.Principal.AWS` with the `API_AWS_IAM_USER_ARN` value retrieved from Snowflake. Additionally, add the following to the `Statement.Condition` field:

    ```{json}
    {
        "StringEquals": {
            "sts:ExternalId": `API_AWS_EXTERNAL_ID`  # The actual value retrieved from Snowflake
        }
    }
    ```

8. Lastly, return to Snowflake and create the external function by running the following query:

    ```{sql}
    create or replace external function decode_abi_input_parameter_prod(inp_str VARCHAR, inp_type VARCHAR)
    RETURNS VARCHAR
    api_integration = <INTEGRATION NAME>
    as 'https://<API GATEWAY ID>.execute-api.<AWS REGION>.amazonaws.com/<API GATEWAY STAGE NAME>/api/v1/abi/decoder';
    ```
