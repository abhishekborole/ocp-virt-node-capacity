"""Authenticated oc transport with explicit context, timeouts, and guarded writes."""
import copy
from datetime import datetime, timezone
from decimal import Decimal
import json
import re
import shutil
import subprocess

VM = 'virtualmachines.kubevirt.io'
VMI = 'virtualmachineinstances.kubevirt.io'
MIG = 'virtualmachineinstancemigrations.kubevirt.io'
SNAP = 'virtualmachinesnapshots.snapshot.kubevirt.io'


def quantity(value):
    match = re.fullmatch(r'([+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)([a-zA-Z]*)', str(value))
    if not match: raise ValueError('Unsupported Kubernetes quantity: ' + str(value))
    units = {'':1, 'n':Decimal('1e-9'), 'u':Decimal('1e-6'), 'm':Decimal('0.001'),
             'k':10**3, 'K':10**3, 'M':10**6, 'G':10**9, 'T':10**12, 'P':10**15, 'E':10**18,
             'Ki':2**10, 'Mi':2**20, 'Gi':2**30, 'Ti':2**40, 'Pi':2**50, 'Ei':2**60}
    if match[2] not in units: raise ValueError('Unsupported quantity unit')
    return Decimal(match[1]) * units[match[2]]


def age_hours(timestamp):
    if not timestamp: return None
    return round((datetime.now(timezone.utc) - datetime.fromisoformat(timestamp.replace('Z', '+00:00'))).total_seconds()/3600, 2)


def condition(obj, kind):
    return next((item for item in obj.get('status', {}).get('conditions', []) if item.get('type') == kind), {})


def require_name(args):
    if not args.name: raise ValueError('--name is required for this operation')
    return args.name


def stopped(client, name):
    if client.get(VMI, name, missing_ok=True):
        raise ValueError('Stop the VM through the supported VM lifecycle workflow before changing its template')


def escape(value):
    return value.replace('~', '~0').replace('/', '~1')


class Client:
    def __init__(self, context, namespace, timeout=60):
        self.context, self.namespace, self.timeout = context, namespace, timeout

    def command(self, *args, data=None, raw=False):
        executable = shutil.which('oc')
        if not executable: raise RuntimeError('Install oc and authenticate with oc login before running this script')
        command = [executable, '--context', self.context, '--request-timeout=30s', '-n', self.namespace, *args]
        result = subprocess.run(command, input=json.dumps(data) if data is not None else None,
                                capture_output=True, text=True, timeout=self.timeout, shell=False)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'oc request failed')
        return result.stdout.strip() if raw else json.loads(result.stdout) if result.stdout.strip() else {}

    def get(self, resource, name=None, missing_ok=False, all_namespaces=False):
        args = ['get', resource]
        if name: args.append(name)
        if missing_ok: args.append('--ignore-not-found')
        if all_namespaces: args.append('-A')
        return self.command(*args, '-o', 'json')

    def items(self, resource, all_namespaces=False):
        return self.get(resource, all_namespaces=all_namespaces).get('items', [])

    def patch(self, resource, original, operations, apply=False):
        version = original['metadata']['resourceVersion']
        patch = [{'op':'test', 'path':'/metadata/resourceVersion', 'value':version}, *operations]
        plan = {'operation':'patch', 'resource':resource, 'name':original['metadata']['name'], 'namespace':self.namespace, 'context':self.context, 'patch':patch, 'applied':False}
        if apply:
            updated = self.command('patch', resource, original['metadata']['name'], '--type=json', '-p', json.dumps(patch), '-o', 'json')
            plan.update(applied=True, resource_version=updated['metadata']['resourceVersion'])
        return plan

    def create(self, manifest, apply=False):
        manifest = copy.deepcopy(manifest)
        manifest.setdefault('metadata', {})['namespace'] = self.namespace
        plan = {'operation':'create', 'context':self.context, 'manifest':manifest, 'applied':False}
        if apply:
            created = self.command('create', '-f', '-', '-o', 'json', data=manifest)
            plan.update(applied=True, name=created['metadata']['name'], uid=created['metadata']['uid'])
        return plan


def migration(client, vmi, apply):
    if vmi.get('status', {}).get('phase') != 'Running' or condition(vmi, 'LiveMigratable').get('status') != 'True':
        raise ValueError('VMI is not Running with LiveMigratable=True; inspect its conditions')
    active = [item for item in client.items(MIG) if item.get('spec', {}).get('vmiName') == vmi['metadata']['name'] and item.get('status', {}).get('phase') not in ('Succeeded','Failed')]
    if active: raise ValueError('An active migration already exists for this VMI')
    return client.create({'apiVersion':'kubevirt.io/v1','kind':'VirtualMachineInstanceMigration',
                          'metadata':{'generateName':vmi['metadata']['name'] + '-admin-'},
                          'spec':{'vmiName':vmi['metadata']['name']}}, apply)
