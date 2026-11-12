---
tags: systemd
date: "2023-11-19"
category: Linux
author: Carlos Neto
title: "Systemd Drop-in Overrides: Customize Unit Properties Without Editing the Unit File"
description: "How to customize a systemd service with an override.conf drop-in instead of editing the unit file, how systemctl edit creates it, and a hands-on example that overrides an EnvironmentFile."
myst:
  html_meta:
    description: "How to customize a systemd service with an override.conf drop-in instead of editing the unit file, how systemctl edit creates it, and a hands-on example that overrides an EnvironmentFile."
og:title: "Systemd Drop-in Overrides: Customize Unit Properties Without Editing the Unit File"
og:description: "How to customize a systemd service with an override.conf drop-in instead of editing the unit file, how systemctl edit creates it, and a hands-on example that overrides an EnvironmentFile."
---

*__Blog Post Publish Date:__ 2023/11/19*

---

# Systemd Drop-in Overrides: Customize Unit Properties Without Editing the Unit File

This blog post covers a cleaner way to customize a systemd service. Instead of editing the unit file, you put your changes in an `override.conf` drop-in file that systemd merges on top of the original. It explains why direct edits cause problems, how overrides work, and walks through a hands-on example.

## Why Editing the Unit File Directly Causes Problems

Sometimes you need to change a property of a systemd service, such as an environment variable that raises the debug level while you troubleshoot. The traditional way is to edit the unit file directly. For example, to change a Docker property, you edit `/etc/systemd/system/docker.service`, reload systemd with `$ systemctl daemon-reload`, and restart the service with `$ systemctl restart docker`.

That works, but it causes a few problems:

- Editing the default unit file makes it easier to break the service with a wrong setting.
- Custom changes are hard to spot later if nobody commented them.
- A package update can replace the unit file and silently drop your changes. Package managers such as [rpm](https://rpm.org/) or [apt](https://wiki.debian.org/Apt) own those files.

## How Systemd Overrides Work

A **drop-in file** is a `.conf` file in a `<unit>.d/` directory that systemd reads after the unit file and merges on top of it. As the [systemd.unit documentation](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html) describes, this lets you change unit properties while the original file stays untouched.

The convention for overrides is this path:

```text
/etc/systemd/system/<UNIT-SERVICE-NAME>.service.d/override.conf
```

> _`<UNIT-SERVICE-NAME>` is a placeholder._

Properties in `override.conf` take precedence over the ones in `<UNIT-SERVICE-NAME>.service`. There is one catch: settings that accept a list, such as `ExecStart=`, add to the original value instead of replacing it. To replace them, first assign an empty value to reset the list, then set the new one. The example below shows the default unit and the override side by side:

::::{grid}

:::{grid-item-card}
- __Default Properties__
```{code-block} ini
:caption: /etc/systemd/system/my-script.service

[Unit]
Description=My script
; collapsed parameters...

[Service]
ExecStart=/usr/local/bin/my-script.sh --prod

[Install]
; collapsed parameters...
```
:::

:::{grid-item-card}
- __Override Properties__
```{code-block} ini
:caption: /etc/systemd/system/my-script.service.d/override.conf

[Service]
ExecStart=
ExecStart=/usr/local/bin/my-script.sh --dev
```
:::

::::

When `my-script.service` starts, it runs `my-script.sh --dev`. The empty `ExecStart=` in `override.conf` clears the command from the unit file, and the next line sets the new one.

The [`systemctl edit`](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html) command is the shortcut for all of this. `$ systemctl edit <UNIT-SERVICE-NAME>` creates `/etc/systemd/system/<UNIT-SERVICE-NAME>.service.d/override.conf`, opens your editor, and runs `$ systemctl daemon-reload` for you when you close it. The only step left is `$ systemctl restart <UNIT-SERVICE-NAME>` when the change needs a restart.

## Hands-On: Overriding an EnvironmentFile

This example creates a service called `my-script` and then overrides where it reads its environment variables from. It uses these files:

```{code-block} bash
/tmp/my-script/env_custom.env           # env vars source of the my-script process
/tmp/my-script/env_default.env          # other env vars source of the my-script process
/tmp/my-script/my-script.sh             # script that my-script process run
/etc/systemd/system/my-script.service   # unit service file definition
```

> _<i class="fa-solid fa-link"></i> The files are on my GitHub: <i class="fa-brands fa-github"></i> [c-neto/my-devops-labs/blog/2023-11-19](https://github.com/c-neto/my-devops-labs/tree/main/blog/2023-11-19/)_

First, create the working directory for the script:

```{code-block} bash
$ mkdir /tmp/my-script/
```

Then create the script itself. It prints two environment variables every second:

```{code-block} bash
:caption: $ vim /tmp/my-script/my-script.sh

#!/bin/bash

while true; do
  echo ">>> $APP_NAME - $MY_CUSTOM_ENV_VAR"
  sleep 1
done
```

Make it executable:

```{code-block} bash
$ chmod +x /tmp/my-script/my-script.sh
```

Next, create the two files that will provide environment variables to the service:

::::{grid}

:::{grid-item-card}
```{code-block} bash
:caption: $ vim /tmp/my-script/env_default.env

APP_NAME="My Awesome Script"
MY_CUSTOM_ENV_VAR="Irish Blood"
```
:::

:::{grid-item-card}
```{code-block} bash
:caption: $ vim /tmp/my-script/env_custom.env

MY_CUSTOM_ENV_VAR="English Heart"
```
:::

::::

Now create the unit file. `ExecStart=` uses the absolute path of the script, because systemd does not search `WorkingDirectory` for the executable.

```{code-block} ini
:caption: $ vim /etc/systemd/system/my-script.service

[Service]
WorkingDirectory=/tmp/my-script/
ExecStart=/tmp/my-script/my-script.sh
EnvironmentFile=/tmp/my-script/env_default.env

[Install]
WantedBy=multi-user.target
```

Reload systemd so it picks up the new unit, then start the service:

```{code-block} bash
$ systemctl daemon-reload
$ systemctl start my-script
```

The log shows the values from `env_default.env`:

```{code-block} bash
:caption: $ journalctl -u my-script -f

Nov 19 16:11:29 fedora my-script.sh[33631]: >>> My Awesome Script - Irish Blood
Nov 19 16:11:30 fedora my-script.sh[33631]: >>> My Awesome Script - Irish Blood
```

Now override the environment file. Create the drop-in directory:

```{code-block} bash
$ mkdir /etc/systemd/system/my-script.service.d/
```

Then add a second `EnvironmentFile` in `override.conf`:

```{code-block} ini
:caption: $ vim /etc/systemd/system/my-script.service.d/override.conf
[Service]
EnvironmentFile=/tmp/my-script/env_custom.env
```

After `$ systemctl daemon-reload` and `$ systemctl restart my-script`, the log changes:

```{code-block} bash
:caption: $ journalctl -u my-script -f

Nov 19 16:21:42 fedora my-script.sh[58573]: >>> My Awesome Script - English Heart
Nov 19 16:21:43 fedora my-script.sh[58573]: >>> My Awesome Script - English Heart
```

`EnvironmentFile=` is a list setting, so the override adds `env_custom.env` after `env_default.env` instead of replacing it. Both files are read, and when the same variable appears in both, the [later file wins](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html). That is why `APP_NAME` still comes from `env_default.env`, while `MY_CUSTOM_ENV_VAR` now comes from `env_custom.env`.

## Why I Prefer Overrides

Overrides keep the original unit file intact and put every custom setting in one explicit place. When something breaks, `$ systemctl cat <UNIT-SERVICE-NAME>` shows the unit file and every drop-in, so you can see right away what was changed. They also survive package updates, because the package manager (dnf, apt, brew) only owns the original unit file, not your drop-in.

`$ systemctl edit` makes the whole process quick: one command to create the file, edit it, and reload systemd. For me, it is the default way to change any service I did not write myself. The kubelet is a good example: its log rotation flags can be set as a systemd `Environment=` property, as I show in [Kubernetes Logs Simplified](/blog/2025/2025-06-22-kubernetes-logs-simplified.md), and an override keeps that change out of the packaged unit file.

## Key Takeaways

- Editing a unit file directly makes mistakes harder to spot, and a package update can overwrite your changes.
- A drop-in file at `/etc/systemd/system/<unit>.service.d/override.conf` is merged on top of the unit file, which stays untouched.
- `$ systemctl edit <unit>` creates the drop-in, opens your editor, and reloads systemd.
- List settings such as `ExecStart=` and `EnvironmentFile=` are added to, not replaced. Assign an empty value first to reset them.
- With several `EnvironmentFile=` entries, a variable from a later file overrides the same variable from an earlier one.
- `$ systemctl cat <unit>` shows the unit file and all its drop-ins together.

## References

- [systemd.unit: drop-in files (systemd)](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html)
- [systemd.exec: EnvironmentFile= (systemd)](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html)
- [systemctl: edit and cat commands (systemd)](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html)
- [systemd project (systemd.io)](https://systemd.io/)
- [systemd cheat sheet (Red Hat)](https://access.redhat.com/sites/default/files/attachments/12052018_systemd_6.pdf)
- [Lab files for this post (GitHub)](https://github.com/c-neto/my-devops-labs/tree/main/blog/2023-11-19/)

*I'm Carlos Neto, and this blog is where I share my experiences and open source contributions. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*

---

```{raw} html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "headline": "Systemd Drop-in Overrides: Customize Unit Properties Without Editing the Unit File",
      "description": "How to customize a systemd service with an override.conf drop-in instead of editing the unit file, how systemctl edit creates it, and a hands-on example that overrides an EnvironmentFile.",
      "datePublished": "2023-11-19",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2023/2023-11-19-systemd-override-parameters/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2023/2023-11-19-systemd-override-parameters/",
      "keywords": ["systemd", "override.conf", "systemctl edit", "drop-in", "Linux"],
      "author": {"@id": "https://carlosneto.dev/#person"}
    },
    {
      "@type": "Person",
      "@id": "https://carlosneto.dev/#person",
      "name": "Carlos Neto",
      "url": "https://carlosneto.dev/",
      "sameAs": ["https://www.linkedin.com/in/c-neto/", "https://github.com/c-neto"]
    },
    {
      "@type": "BreadcrumbList",
      "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://carlosneto.dev/"},
        {"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://carlosneto.dev/blog/"},
        {"@type": "ListItem", "position": 3, "name": "Systemd Drop-in Overrides: Customize Unit Properties Without Editing the Unit File"}
      ]
    }
  ]
}
</script>
```
