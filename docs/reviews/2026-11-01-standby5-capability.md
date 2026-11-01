# Separate Standby type 5 capability assessment — November 1, 2026

**Capability assessment complete; physical type 5 not exercised / unverified.**
No supported procedure was established for selecting Standby 5 on this target.
The public ARM64 default policy selects Deep Idle 7 or Hibernate 4. Both have
actual target-Mac evidence. Do not claim a physical Standby pass, universal
hardware impossibility or complete milestone acceptance from this assessment.

User said **"go ahead and test it"** immediately after the Hibernate result and
the separate Standby caveat. Interpreted this as a request for the separate type
5 condition. Before starting another countdown or changing settings, checked
target capabilities, registry/state history and Apple's platform policy.

## Target observations

Actual **Mac15,9, ARM64_T6031**, macOS **26.6.2 (25G83)**, Darwin **25.6.0**;
`sysctl kern.version` identifies **xnu-12377.161.14~5/RELEASE_ARM64_T6031**.
Read-only commands:

```sh
pmset -g cap
pmset -g custom
pmset -g log
ioreg -r -c IOPMrootDomain -d 1
sysctl kern.osrelease kern.osversion hw.model hw.machine
sysctl -n kern.version
```

Only selected registry keys and aggregate/named state events were retained, not
the entire registry or other applications' power requests. Both battery/AC profiles
remain hibernatemode 3, standby 1; every parsed setting still matches the original
snapshot from before the controlled Hibernate test. Last recorded sleep type is
4 after that test. No separate policy-handler registration property was observed.
October 31/November 1 retained wake-category counts: **161 Deep Idle, one Hibernate,
zero Standby**. Counts are log entries, not necessarily unique sleep intervals.
The generic standby preference/capability name does not itself prove that the
platform's state-selection policy exposes the separate numeric type 5.

## Published platform policy

Reviewed Apple's [IOPMrootDomain implementation](https://github.com/apple-oss-distributions/xnu/blob/xnu-12377.121.6/iokit/Kernel/IOPMrootDomain.cpp)
and current public main source. In published tag **xnu-12377.121.6**, the
`__arm64__` default handler at lines **587–603** selects Deep Idle initially and
Hibernate for forced hibernation or a low-battery condition. It contains no type-5
selection. The source initializes the handler to that function for ARM64; its
registration path rejects another handler when one is already installed. The
legacy standby-policy-table path does not establish a supported type-5 trigger
for this default ARM64 path. No kernel/driver modification is proposed.

Version limit: public tag metadata returned xnu-12377.121.6 and earlier family
tags; the running xnu-12377.161.14 tag was absent from the first 100 published
tags. The installed binary is newer than the reviewed version. This is a
source-supported platform assessment corroborated by this Mac's actual 7/4
observations, not a byte-for-byte proof of every private path in the installed
kernel. Therefore the recorded conclusion is **no documented supported trigger
established**, rather than an absolute unsupported-hardware certification.

Static source check, exit 0:

```sh
.venv/bin/python .evidence/mac-verification-20261101/standby5-capability/check_policy.py
```

It extracts the fixed-version ARM64 handler and verifies its referenced selected
sleep types are exactly DeepIdle/Hibernate. This is source analysis, not simulated
or actual Standby evidence. Exact files, SHA-256 hashes, family tag metadata,
host assessment and check source retained in the evidence folder above. Downloaded
main and fixed-version source are separately hashed; they are not identical files.

The first Python HTTPS fetch failed because that interpreter's CA lookup could
not validate the certificate. The system curl client then fetched the public
Apple sources successfully with normal certificate verification; no TLS check or
system security setting was disabled. This retrieval issue was not an app failure.

## Decision and correction to earlier guidance

Earlier guidance treated `standby 1` as enough reason to keep a separate type-5
manual test on the target-Mac list. That inference was too broad: a preference
name is not the same as an exposed state-selection branch. The platform policy
should have been checked before suggesting repeated lid cycles for this label.
Historical observations and review decisions remain preserved.

There is **no actionable additional type-5 physical test established through the
supported controls reviewed for this Mac**. Do not repeat an unchanged overnight
cycle, shorten unverified standby-delay keys, drain the battery, replace kernel
policy or relabel Hibernate 4 as Standby 5. Record type 5 as unexercised with this
platform limitation; include the limitation explicitly when deciding candidate
acceptance scope. This is a recommendation for scope review, not a silent full
M2/M3 gate pass or rewrite of the runbook's evidence requirements.

No new observer/service/countdown or power-setting change was made. Actual Deep
Idle/maintenance-wake and Hibernate recovery passes remain valid. Current power
settings match the pre-test originals, with no temporary helper remaining from
the completed test. No application/test source change, suite rerun, personal-data
operation, commit or push. Existing user edits/index/stashes preserved. Scoped
documentation links/whitespace and retained evidence manifest checked. Next is
final planner/trial-readiness review with this limitation stated explicitly.
