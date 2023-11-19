---
tags: systemd
date: "2023-11-19"
category: Linux
---

*__Blog Post Publish Date:__ 2023/11/19*

---

# Properties Overriding: A Smart Way to Customize Systemd Unit Properties

This blog post covers an smart alternative to customize systemd unit process parameters.

This blog post delivers a explanation of the systemd `override.conf` file. It elucidates the drawbacks of directly altering unit service configurations, introduces the overriding approach as a solution, presents a practical, hands-on example, and culminates with my personal perspective on the effectiveness of this structural methodology.

## Drawbacks of Direct Unit Service Editing

At times, there's a need to modify certain properties within a particular systemd unit service, such as adjusting the value of an environment variable to enhance debug levels for troubleshooting. Traditionally, this involves directly altering the unit service file. For instance, if you wish to modify properties of Docker, you'd edit `/etc/systemd/system/docker.service`, implement the changes, refresh systemd with `$ systemctl daemon-reload`, and then restart the Docker process using `$ systemctl restart docker`.

While this approach functions adequately, it introduces certain behaviors that may pose issues depending on your use case.

- Modifying default unit services elevates the risk of configuring settings incorrectly.
- Custom changes can be challenging to discern if they lack proper comments.
- Unit service files might be overridden based on the installation method. For instance, the unit service could be replaced according to package update definitions of a package manager like [rpm](https://rpm.org/) or [apt](https://wiki.debian.org/Apt).

In the following section, I will elucidate an elegant workaround for these behaviors.

## The Solution: Parameters Overriding

A sophisticated approach to customizing unit service parameters involves overriding them.

This method enables you to make changes to systemd unit properties while preserving the default file without any modifications. This is possible because the method reads custom properties from another file and merges them with the default properties.

Override parameters are declared in the following file pattern:

```
/etc/systemd/system/<UNIT-SERVICE-NAME>.service.d/override.conf
```

> _`<UNIT-SERVICE-NAME>` is a placeholder._

All unit service properties defined in `override.conf` will take precedence over those defined in `<UNIT-SERVICE-NAME>.service`.

Consider the following example, where both default and override unit properties are illustrated.

::::{grid}

:::{grid-item-card}
- __Default Properties__
```{code-block} toml
:caption: /etc/systemd/system/my-script.service

...
[Description]
# collapse definitions...

[Service]
ExecStart=my-script.sh --prod

[Install]
# collapse definitions...
```
:::

:::{grid-item-card}
- __Override Properties__
```{code-block} toml
:caption: /etc/systemd/system/my-script.service.d/override.conf

[Service]
ExecStart=my-script.sh --dev
```
:::

::::

When the `my-script.service` be executed, the _ExecStart_ command will be `my-script.sh --dev` because it were declared in the `override.conf` that replace the _ExecStart_ defined in the `my-script.service`.

---

An efficient shortcut to execute this action is through the `$ systemctl edit <UNIT-SERVICE-NAME>` command.

This command creates a directory and file at `/etc/systemd/system/<UNIT-SERVICE-NAME>.service.d/override.conf`, opens your text editor for making the necessary changes, and upon closing it, automatically executes `$ systemctl daemon-reload` behind the scenes. The only additional step is to execute `$ systemctl restart UNIT-NAME` when necessary to apply the changes.

## Hands On

Let's get hands-on! This section will delve into a detailed example of the override method.

We will create a systemd unit service named `my-script`. To achieve this, we need to create the following files:

```{code-block} bash
/tmp/my-script/env_custom.env           # env vars source of the my-script process
/tmp/my-script/env_default.env          # other env vars source of the my-script process
/tmp/my-script/my-script.sh             # script that my-script process run
/etc/systemd/system/my-script.service   # unit service file definition
```

> _<i class="fa-solid fa-link"></i> The files can be found on my GitHub: <i class="fa-brands fa-github"></i> [c-neto/my-devops-labs/blog/2023-11-19](https://github.com/c-neto/my-devops-labs/tree/main/blog/2023-11-19/)_


Initially, let's create the working directory for the script.

```{code-block} bash
$ mkdir /tmp/my-script/
```

Following that, we'll generate the source code for the script.

```{code-block} bash
:caption: $ vim /tmp/my-script/my-script.sh

#!/bin/bash

while true; do
  echo ">>> $APP_NAME - $MY_CUSTOM_ENV_VAR"
  sleep 1
done
```

Assign the source code to the execution file parameter.

```{code-block} bash
$ chmod +x /tmp/my-script/my-script.sh
```

We will create two files that will serve as the source for environment variables in the `my-script` unit service.

::::{grid}

:::{grid-item-card}
```{code-block} bash
:caption: $ vim /tmp/my-script/env_default.env

APP_NAME="my-script"
MY_CUSTOM_ENV_VAR="irish blood"
```
:::

:::{grid-item-card}
```{code-block} bash
:caption: $ vim /tmp/my-script/env_custom.env

MY_CUSTOM_ENV_VAR="england heart"
```
:::

::::

---

Next, we will create the systemd unit service file.

```{code-block} bash
:caption: $ vim /etc/systemd/system/my-script.service

[Service]
WorkingDirectory=/tmp/my-script/
ExecStart=my-script.sh
EnvironmentFile=/tmp/my-script/env_default.env

[Install]
WantedBy=multi-user.target
```

Now, let's reload the systemd daemon so that `my-script` can be managed as a service by systemd, and then start it.

```
$ systemctl daemon-reload
$ systemctl start my-script
```

To inspect the log of `my-script`, you can verify the value of the `/tmp/my-script/env_default.env` file.

```{code-block} bash
:caption: $ journalctl -u my-script -f

Nov 19 16:11:29 fedora my-script.sh[33631]: >>> irish blood
Nov 19 16:11:30 fedora my-script.sh[33631]: >>> irish blood
```

Next, we will override the source file for environment variables.

```
$ mkdir /etc/systemd/system/my-script.service.d/
```

We will override the `EnvironmentFile` parameter.

```{code-block} bash
:caption: $ vim /etc/systemd/system/my-script.service.d/override.conf
[Service]
EnvironmentFile=/tmp/my-script/env_custom.env
```

This time, variables from the `env_custom.env` file will replace those present in the `env_default.env` file.

```{code-block} bash
:caption: $ systemctl edit my-script

Nov 19 16:21:42 fedora my-script.sh[58573]: >>> my-script - england heart
Nov 19 16:21:43 fedora my-script.sh[58573]: >>> my-script - england heart
```

## Conclusion (Author Opinion)

In conclusion, leveraging systemd override parameters emerges as an invaluable tool in proactively addressing and preventing recurring issues. By preserving the integrity of the original unit service file while explicitly specifying custom parameters, this method significantly enhances troubleshooting capabilities. Another notable advantage lies in safeguarding against the loss of custom configurations that may be tied to the installation manager used to create a unit service (dnf, apt, brew).

The seamless flexibility provided by the `$ systemctl edit` command empowers users to swiftly and efficiently modify process properties, ensuring an agile and responsive approach to system management. In essence, incorporating systemd override parameters not only fortifies system stability but also streamlines the process of adapting and optimizing configurations to meet evolving needs. As a dynamic solution in the realm of systemd, it stands as an essential practice for maintaining a resilient and adaptable system environment.

## Links

- <https://github.com/c-neto/my-devops-labs/tree/main/blog/2023-11-19/>
- <https://systemd.io/>
- <https://access.redhat.com/sites/default/files/attachments/12052018_systemd_6.pdf>
