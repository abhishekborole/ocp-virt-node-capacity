# ocp-virt-node-capacity

Collect node allocatable resources and conservative pod-request upper bounds from the cluster.

Connects to **OpenShift 4.20+ with OpenShift Virtualization** through the installed `oc` CLI and your existing kubeconfig authentication. Reads actual API objects directly; no prepared inventory files or demonstration data are used.

## Connect and run

Requires Python 3.11+, a matching supported `oc` client, and an authenticated account. Log in interactively with `oc login`, then select an existing context using `oc config get-contexts`.

```powershell
python tool.py --context YOUR_CONTEXT --namespace YOUR_NAMESPACE 
```

Replace uppercase arguments with real infrastructure identifiers. Run `python tool.py --help` for all options. The command above previews any requested change. For an implemented change operation, add `--apply` to submit it. With no change-specific option, scripts collect live reports. `--apply` alone never invents an operation.

JSON is written to stdout; redirect it to a local report outside the repository if needed. Errors go to stderr with exit code 2. Exit 0 means the request/report completed, not that asynchronous tasks have completed or all findings are healthy. Kubeconfig credentials are handled by `oc`; the script never accepts or prints a cluster token. Do not publish collected infrastructure reports.

## Permissions and behavior

Required RBAC: **cluster-wide list nodes and pods**. Use the smallest role covering the operation. API errors are reported directly and are not converted into healthy results. Context and namespace are explicit on every command. Requests time out; writes are never automatically retried. VM/PVC/node patches include a resourceVersion test so concurrent changes fail instead of being overwritten.

Adds init-container requests conservatively rather than reproducing every scheduler admission rule. This is request accounting, not live utilization or a placement guarantee.

## Verification

```console
python -m unittest discover -v
```

Tests mock command responses to verify transport boundaries, explicit targeting, quantity handling, migration gates, and preview behavior. They are software tests, not claims of connection to a live lab. OpenShift/MTV/OADP feature availability and RBAC must be verified on your installed versions before applying changes. CI runs these tests without infrastructure secrets; it never operates your cluster.

## References

- [OpenShift 4.20 virtualization documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/virtualization/index)
- [KubeVirt API reference](https://kubevirt.io/api-reference/main/definitions.html)
- [KubeVirt live migration](https://kubevirt.io/user-guide/compute/live_migration/)
- [Snapshot API](https://kubevirt.io/user-guide/storage/snapshot_restore_api/)
- [MIT license](LICENSE)
