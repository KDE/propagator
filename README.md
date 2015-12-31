![Propagator - A KDE Project](docs/logo.png "Propagator - A KDE Project")

## What is Propagator?

Propagator is a Git mirror fleet manager. Every time someone pushes a commit to a central read-write Git server, Propagator propagates that commit to a fleet of read-only git mirror servers, as well as to GitHub.

Propagator was built with ♥ at [KDE](https://www.kde.org/), where we use it to propagate updates in near real-time to our fleet of `anongit.kde.org` servers, as well as to our read-only [GitHub mirror](https://github.com/kde/).

## Quickstart

Propagator runs on your main Git server, i.e., the one that has the repositories on disk, and to which users can push commits. This is important, since Propagator is notified of repository updates through the repo's `post-recieve` or `post-update` hooks.

Running Propagator is easy. You'll need to have to following installed:

* Python 3.5 (Propagator uses the AsyncIO module)
* RabbitMQ
* Celery 3
* GitPython
* OpenSSH Client
* Supervisord

To install, simply clone this repository locally, `cd` into it, and edit the configuration at `config/ServerConfig.json`. Then you can run the server by executing:

    $: supervisord -c ./supervisord.conf

The default configuration shipped in the repository explicitly disables daemonization of the Supervisord process, but you can re-enable that in `supervisord.conf`.

## Anongit Servers

On the Anongit servers (mirrors), we use a small SSH agent to remotely create, move, or delete repositories, or change descriptions.

The agent is available at `agent/GatorSSHAgent`, and is a single self-contained Python 3.3+ script whose only external dependency is GitPython. You can simply copy this script to your Anongit servers independently of the rest of the project.

To set up the agent to talk to the server, here's what you have to do:

1. First, generate a new SSH keypair and copy the public key to the server's `~/.ssh/authorized_keys` file. Do **NOT** re-use your existing SSH key. This is important.
2. On the Propagator server, edit the configuration to point to the private key file. The relevant entry is `AnongitAPIKeyFile` in `config/ServerConfig.json`.
3. On the mirror, edit the `~/.ssh/authorized_keys` and **prefix** the entry for this public key with `command=/path/to/GatorSSHAgent`. The entry should look like this: `command=/path/to/GatorSSHAgent ssh-rsa AbbcDEfgggHHj... your@ssh-key-comment`.

Of course, this only handles the management of repositories on the servers. Pushes are done over the standard ssh+git mechanism. This is why you need a separate key for the control API - OpenSSH uses the key to discern between a shell or git login or a control API login.

## Updating Repositories

Once the server is up and running, and Anongit servers have been configured with the SSH agent, you'll want to actually push updates to your fleet.

Propagator can create repositories on remotes on first push, so you don't have to create repositories on the remotes manually.

In your repo's `post-recieve` or `post-update` hook, simply add this command:

    ${PROPAGATOR_REPO}/bin/mirrorctl update reponame.git

Where `${PROPAGATOR_REPO}` is the location to where you've cloned the Propagator repository, and `reponame.git` is the repository that you want to update on your remotes.

And that's it.

## Maintainership

Propagator is currently maintained by Boudhayan Gupta (<bgupta@kde.org>). It is not part of any KDE release module, and tarballs are released independently as and when major releases are warranted.
