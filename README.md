SANTools
========

Python tools for interacting with various SANs directly.

There are two basic packages/paths:
SANTools: where the primary code for interacting with the SAN lives.
The sanclient is the base class that SAN-specific implementations should extend.
The current implementation only contains an EMC VNX extension, vnxclient.

SANTests: for implementing tests that use SANTools to separate the test and core code.

You will have to add SANTools to your PYTHONPATH to use SANTests in its current form. That will be fixed soon.

The current EMC VNX implementation requires that you have the EMC Navisphere Secure CLI installed on the local machine
and that it is installed at /opt/Navisphere/bin/naviseccli
