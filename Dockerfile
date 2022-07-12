FROM public.ecr.aws/lambda/python:3.9

# gcc is dependency for lru-dict python module
RUN yum install gcc -y

COPY pyproject.toml ./

RUN pip install poetry

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

COPY src/handlers.py ./

# You can overwrite command in `serverless.yml` template
CMD ["handlers.to_signature_handler"]