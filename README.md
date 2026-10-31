# ocp-virt-node-capacity

Estimate remaining allocatable CPU and memory after a proposed VM batch.

An independent OpenShift Virtualization lab utility using Python 3.11+ and the standard library. All examples are synthetic. This tool performs offline analysis and does not require credentials.

## Run

```console
python tool.py examples/sample.json
python -m unittest discover -v
```

Run from this repository directory. Output is JSON on stdout. Exit 0 means analysis completed, including when findings are present; exit 2 means invalid input or an unreadable file. Inspect result fields for policy findings. See [expected output](examples/expected.json).

## Input contract

Supply normalized JSON matching [sample.json](examples/sample.json). This is a purpose-built interchange format, not an unmodified `oc`, Kubernetes API, vCenter, or PowerCLI export. Map your lab exports to these documented fields before use. Numeric units are part of field names. Ages and observed statuses must be calculated by the data collector.

| Required field | Type |
| --- | --- |
| `allocatable_cpu` | integer |
| `allocatable_memory_gib` | integer |
| `used_cpu` | integer |
| `used_memory_gib` | integer |
| `new_cpu` | integer |
| `new_memory_gib` | integer |

All listed fields are required on each matching record; additional keys are allowed. Lists may be empty unless the algorithm requires at least one record. Nonnegative sample numbers require nonnegative input. Booleans must be JSON booleans. Thresholds are local examples, not vendor defaults or universal recommendations.

## Example result

```json
{
  "fits": true,
  "remaining_cpu": 16,
  "remaining_memory_gib": 80
}
```

## Scope and limits

The calculation is implemented in `_analyze` in [tool.py](tool.py). Read its checks before applying the result to a real environment. The result describes only supplied records, not overall platform health, compatibility, security, or supportability. Incomplete or stale exports can hide problems. Capacity and transfer estimates omit platform overhead, reservations, contention, dirty-page rates, and other constraints unless explicitly represented by an input field. Greedy placement is a planning heuristic and can miss a feasible arrangement.

This is a focused initial implementation with fixture and CLI tests, not a production-certified integration. No infrastructure changes are made by this utility.

## Development

Tests cover the example, a changed workload, invalid input, missing files, CLI behavior, and input immutability. CI is configured for Python 3.11 and 3.13 on Linux and Windows; local results are recorded in the workspace portfolio report. Contributions should add representative sanitized fixtures and tests for new behavior. Never commit infrastructure credentials or production exports.

## References

- [Platform or language documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/virtualization/index) — verify behavior against your deployed version.
- [MIT license](LICENSE)
