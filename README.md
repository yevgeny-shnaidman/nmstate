# We are nmstate!
A declarative network manager API for hosts.

[![Build Status](https://travis-ci.org/nmstate/nmstate.png?branch=master)](https://travis-ci.org/nmstate/nmstate)
[![Coverage Status](https://coveralls.io/repos/github/nmstate/nmstate/badge.svg?branch=master)](https://coveralls.io/github/nmstate/nmstate?branch=master)

## What is it?
NMState is a library with an accompanying command line tool that manages
host networking settings in a declarative manner.
The networking state is described by a pre-defined schema.
Reporting of current state and changes to it (desired state) both conform to
the schema.

NMState is aimed to satisfy enterprise needs to manage host networking through
a northbound declarative API and multi provider support on the southbound.
NetworkManager acts as the main (and currently the only) provider supported.

## Development Environment

Install:
```shell
pip install tox pbr
```

Run Unit Tests:
```shell
tox
```

## Runtime Environment

Install (from sources):
```shell
sudo pip install .
```

## Basic Operations

Show current state:
```shell
nmstatectl show
```

Change to desired state:
```shell
nmstatectl set --file <desired-state.json>
```

Desired/Current state example:
```shell
{
    "interfaces": [
        {
            "ipv4": {
                "addresses": [
                    {
                        "ip": "192.168.122.1",
                        "prefix-length": 24
                    }
                ],
                "enabled": true
            },
            "name": "eth0",
            "state": "up",
            "type": "ethernet"
        }
    ]
}
```

## Supported Interfaces:
- bond
- dummy
- ethernet