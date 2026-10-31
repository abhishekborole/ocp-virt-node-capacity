import json
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from oc_client import Client, quantity, escape, migration


class TransportTests(unittest.TestCase):
    def test_preview_never_writes(self):
        client = Client('production-context','workloads')
        with patch.object(client,'command') as command:
            plan = client.patch('nodes',{'metadata':{'name':'worker','resourceVersion':'7'}},[{'op':'add','path':'/spec/unschedulable','value':True}])
            command.assert_not_called()
        self.assertFalse(plan['applied'])
        self.assertEqual(plan['patch'][0],{'op':'test','path':'/metadata/resourceVersion','value':'7'})

    @patch('oc_client.shutil.which',return_value='oc')
    @patch('oc_client.subprocess.run')
    def test_context_namespace_and_timeout_are_pinned(self, run, which):
        run.return_value = SimpleNamespace(returncode=0,stdout='{"items":[]}',stderr='')
        self.assertEqual(Client('selected','only-this-namespace').items('pods'),[])
        args,options = run.call_args
        self.assertIn('selected',args[0]); self.assertIn('only-this-namespace',args[0])
        self.assertFalse(options['shell']); self.assertEqual(options['timeout'],60)

    def test_failed_preflight_never_creates_migration(self):
        client = Client('context','namespace')
        with patch.object(client,'create') as create:
            with self.assertRaises(ValueError): migration(client,{'status':{'phase':'Pending'}},True)
            create.assert_not_called()

    def test_create_preview_never_calls_cluster(self):
        client = Client('context','namespace')
        with patch.object(client,'command') as command:
            plan = client.create({'kind':'VirtualMachineSnapshot','metadata':{'name':'snapshot'}})
            command.assert_not_called()
        self.assertEqual(plan['manifest']['metadata']['namespace'],'namespace')

    def test_quantities_and_json_pointer(self):
        self.assertEqual(quantity('1Gi'),1073741824)
        self.assertEqual(quantity('500m'),quantity('0.5'))
        self.assertEqual(escape('example.com/key'),'example.com~1key')
        with self.assertRaises(ValueError): quantity('garbage')


if __name__ == '__main__': unittest.main()
