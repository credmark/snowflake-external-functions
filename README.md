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
