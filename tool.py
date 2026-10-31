"""Collect node allocatable resources and conservative pod-request upper bounds from the cluster."""
import argparse
from decimal import Decimal
import json
import sys
import subprocess
from datetime import datetime, timezone
from oc_client import Client, VM, VMI, MIG, SNAP, quantity, age_hours, condition, require_name, stopped, escape, migration


def execute(client,args):
    totals = {}
    for pod in client.items('pods', all_namespaces=True):
        node = pod.get('spec', {}).get('nodeName')
        if not node or pod.get('status', {}).get('phase') in ('Succeeded','Failed'): continue
        total = totals.setdefault(node, {'cpu':Decimal(0), 'memory':Decimal(0)})
        for container in pod.get('spec', {}).get('containers', []) + pod.get('spec', {}).get('initContainers', []):
            requests = container.get('resources', {}).get('requests', {})
            for key in total: total[key] += quantity(requests.get(key, 0))
        for key in total: total[key] += quantity(pod.get('spec', {}).get('overhead', {}).get(key, 0))
    return [{'name':node['metadata']['name'], 'unschedulable':node.get('spec', {}).get('unschedulable', False), 'ready':condition(node,'Ready').get('status'),
             'allocatable_cpu':str(quantity(node['status']['allocatable']['cpu'])), 'allocatable_memory_bytes':str(quantity(node['status']['allocatable']['memory'])),
             'conservative_requested_cpu':str(totals.get(node['metadata']['name'], {}).get('cpu',0)), 'conservative_requested_memory_bytes':str(totals.get(node['metadata']['name'], {}).get('memory',0))} for node in client.items('nodes')]


def main():
    parser = argparse.ArgumentParser(description='Collect node allocatable resources and conservative pod-request upper bounds from the cluster.')
    parser.add_argument('--context',required=True,help='Explicit existing oc kubeconfig context')
    parser.add_argument('--namespace',required=True,help='Namespace for workload operations')
    parser.add_argument('--name',help='Exact workload/resource name where required')
    parser.add_argument('--apply',action='store_true',help='Execute the requested change; default is preview')

    args = parser.parse_args()
    try:
        result = execute(Client(args.context,args.namespace),args)
        print(json.dumps({'context':args.context,'namespace':args.namespace,'collected_at':datetime.now(timezone.utc).isoformat(),'result':result},indent=2))
    except (RuntimeError,ValueError,KeyError,OSError,TimeoutError,subprocess.SubprocessError) as error:
        print(str(error),file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__': raise SystemExit(main())
