---
tags: python, dynaconf
date: "2024-07-21"
category: Code
---

<i class="fa fa-calendar"></i> *__Blog Post Publish Date:__ 2024/07/21*

---

# Dynaconf: The Python Settings Siver Bullet! 

This blog post outlines how to extending the Dynaconf to load parameters from multiple and costum sources.

## Good Practices in Application Settings

The definitively best practice guide for Application settings is the [12 Factor](https://12factor.net/config) definition. In summary, the guide emphasizes the separation of config from code and suggets a set parametrization based on environments needs.

Like almost recurring generic needs and best practices well defined, there are some modules and framework for help us.

In Python world, there are some tools that can help you to achieve these best practices. I can refer some nice tools like [python-dotenv](https://github.com/theskumar/python-dotenv), (_focused in reads simple key-value pairs from a .env file and can set them as environment variables_), and [python-decouple](https://github.com/HBNetwork/python-decouple) (_helps provide a dynamic settings interface to can help to change parameters without having to redeploy your app, useful for web applications_). Besides that, there are built-in modules for parse structured files that can be use as a settings files, like [tomllib](https://docs.python.org/3/library/tomllib.html#module-tomllib), [shlex](https://docs.python.org/3/library/shlex.html#module-shlex), [json](https://docs.python.org/3/library/json.html#module-json).

These modules are really nice, and had your specific use case, mainly with you can use minative approach and simple programs like routine scripts. But, with the provocative blog post title, I will present the Dynaconf.

## Dynaconf

The Dyanconf is more robust module for settings in Python. Your design are created for strict follow 12 Factor config principles. We can understand the Dynaconf as an abstraction layer between code and settings providing a robust and simple code interface.

The main features for me are support from most common settings file format (toml|yaml|json|ini|py), multi and hirarchcal profiles support (like default, development, testing, production), mulitple settings source support useful for isolate sensitive information, environment variable input support (take precedence over than others settings source following the Unix philosophy). In addition, there are a CLI useful for debug or export values.

Dyanconf have built-in support for external parameter/secrets storage system like Hashicorp Vault and Redis. But the Dynaconf provide a extending interface to use any sources based on your needs. This feature is really awesome! I will show an example how to do it.

## Talk is cheap, Show me the code!


Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install dynaconf boto3 
```

Inits a dynaconf project:

```bash
dynaconf init \
    -v PARAMETER_FROM_SETTINGS_TOML_FILE="foobar from settings.toml" \
    -s PARAMETER_FROM_SECRETS_TOML_FILE="foobar from .secrets.toml"
```

The previous command will create the following files:

```bash
├── config.py       # python module that have dynaconf instance
├── .secrets.toml   # settings files that have: PARAMETER_FROM_SECRETS_TOML_FILE
└── settings.toml   # settings files that have: PARAMETER_FROM_SETTINGS_TOML_FILE
```

The `config.py` source code is:

```{code-block} python
:caption: config.py

from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=['settings.toml', '.secrets.toml'],
)
```

Use the dynaconf-cli to list parameters:

```bash
$ dynaconf -i config.settings list 

# >>> Working in main environment 
#
# PARAMETER_FROM_SETTINGS_TOML_FILE<str> 'foobar from settings.toml'
# PARAMETER_FROM_SECRETS_TOML_FILE<str> 'foobar from .secrets.toml'
```

Configure AWS Environment Variables to access the Localstack container.

```bash
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_DEFAULT_REGION=us-east-1
```

Put two parameters in AWS Parameter Store to use in Dynaconf.

```bash
aws ssm put-parameter \
    --name "/my-application/PARAMETER_FROM_AWS_PARAMETER_STORE_1" \
    --value "foo" \
    --type "SecureString" \
    --endpoint-url http://localhost:4566

aws ssm put-parameter \
    --name "/my-application/PARAMETER_FROM_AWS_PARAMETER_STORE_2" \
    --value "bar" \
    --type "SecureString" \
    --endpoint-url http://localhost:4566
```


Edit the `conf.py` with the following content:

```{code-block} python
:caption: config.py

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from dynaconf import Dynaconf, LazySettings
import logging

# Configure logging
logger = logging.getLogger(__name__)


def _aws_parameter_store_loader(parameters_prefix="/my-application/") -> dict:
    ssm_client = boto3.client('ssm')

    paginator = ssm_client.get_paginator("get_parameters_by_path")
    parameters_from_aws = {}

    for page in paginator.paginate(Path=parameters_prefix, Recursive=True, WithDecryption=True):
        for param in page["Parameters"]:
            param_name_full = param["Name"]
            param_value = param["Value"]

            try:
                *_, param_name = param_name_full.split("/")
            except ValueError:
                logger.warning('Parameter name pattern outside of expected format, skipping: "{param_name_full}"')
                continue

            parameters_from_aws[param_name] = param_value

    return parameters_from_aws


def load(obj: LazySettings, env: str, silent: bool = True, key: str = None, filename: str = None) -> None:
    global parameters_from_aws

    logger.debug(f"Parameters loaded from AWS Parameter Store: {list(parameters_from_aws)}")
    obj.update(parameters_from_aws)


# Attempt to load parameters from AWS Parameter Store and update Dynaconf loaders
try:
    parameters_from_aws = _aws_parameter_store_loader(ssm_client)
except (BotoCoreError, ClientError) as e:
    LOADERS_FOR_DYNACONF = ["dynaconf.loaders.env_loader"]
    logger.warning("AWS active session not detected, skipping load parameters from AWS Parameter Store")
else:
    LOADERS_FOR_DYNACONF = [__name__, "dynaconf.loaders.env_loader"]

# Initialize Dynaconf settings with specified files and loaders
settings = Dynaconf(
    settings_files=["settings.toml", ".secrets.toml"],
    envvar_prefix="MY_APP",
    LOADERS_FOR_DYNACONF=LOADERS_FOR_DYNACONF,
)
```

Now, check the variables and note the `PARAMETER_FROM_AWS_PARAMETER_STORE_1` and `PARAMETER_FROM_AWS_PARAMETER_STORE_2` that was retrivied from AWS Parameter Store

```bash
$ dynaconf -i config.settings list

# >>> output
#
# PARAMETER_FROM_SETTINGS_TOML_FILE<str> 'foobar from settings.toml'
# PARAMETER_FROM_SECRETS_TOML_FILE<str> 'foobar from .secrets.toml'
# PARAMETER_FROM_AWS_PARAMETER_STORE_1<str> 'foo'
# PARAMETER_FROM_AWS_PARAMETER_STORE_2<str> 'bar'
```

```bash
export MY_APP_PARAMETER_FROM_AWS_PARAMETER_STORE_2="param from environment variable"
```

```bash
$ dynaconf -i config.settings list

# >>> output
#
# PARAMETER_FROM_SETTINGS_TOML_FILE<str> 'foobar from settings.toml'
# PARAMETER_FROM_SECRETS_TOML_FILE<str> 'foobar from .secrets.toml'
# PARAMETER_FROM_AWS_PARAMETER_STORE_1<str> 'foo'
# PARAMETER_FROM_AWS_PARAMETER_STORE_2<str> 'param from environment variable'
```

:::{tip}
I created a lab to exemplify how to use Dynaconf with multiple parameter sources, including custom loaders to retrieve parameters from AWS Parameter Store: <i class="fab fa-github"></i> _[github.com/c-neto/my-code-playground/blog-code-examples/2024-07-20-dynaconf-loaders](https://github.com/c-neto/my-code-playground/tree/main/blog-code-examples/2024-07-20-dynaconf-loaders)_
:::

## Links

- <https://12factor.net>
- <https://12factor.net/config>
- <https://docs.python.org/3/library/json.html>
- <https://docs.python.org/3/library/shlex.html>
- <https://docs.python.org/3/library/tomllib.html>
- <https://github.com/c-neto/my-code-playground/tree/main/blog-code-examples/2024-07-20-dynaconf-loaders>
- <https://github.com/HBNetwork/python-decouple>
- <https://github.com/theskumar/python-dotenv>
