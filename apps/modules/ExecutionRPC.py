"""
    HTTP/WS API interface for simple tasks.
"""
import requests
import json
import time


class RPCMethod(object):
    """
    A generic method that we can send and receive.
    """

    def __init__(self, method, params, _id=1, timeout=5):
        self.payload = {
            "method": method,
            "params": params,
            "jsonrpc": "2.0",
            "id": _id,
        }
        self.timeout = timeout

    def get_response(self, url):
        start = int(time.time())
        while time.time() - start < self.timeout:
            try:
                return requests.post(url, json=self.payload, timeout=self.timeout)

            except requests.ConnectionError:
                # odds are the bootstrapper is trying to connect to a client
                # that is not up already.
                pass
            except requests.Timeout as e:
                # actually timed out.
                raise e


class eth_get_block_RPC(RPCMethod):
    def __init__(self, blk="latest", _id=1, timeout=5):
        super().__init__("eth_getBlockByNumber", [blk, True], _id, timeout)


class admin_node_info_RPC(RPCMethod):
    def __init__(self, _id=1, timeout=5):
        super().__init__("admin_nodeInfo", [], _id, timeout)


class admin_add_peer_RPC(RPCMethod):
    def __init__(self, enode, _id=1, timeout=5):
        super().__init__("admin_addPeer", [enode], _id, timeout)


class admin_peers_RPC(RPCMethod):
    def __init__(self, _id=1, timeout=5):
        super().__init__("admin_peers", [], _id, timeout)


class ExecutionJSONRPC(object):
    """
    A client that represents a single execution endpoint to interact with.
    """

    def __init__(self, endpoint_url, non_error=True, timeout=5):
        self.endpoint_url = endpoint_url
        self.non_error = non_error
        self.timeout = timeout

    def _is_valid_response(self, response):
        if self.non_error:
            if response.status_code == 200:
                if "error" not in response.json():
                    return True
        else:
            return False

    def send_payload(self, rpc):

        start = int(time.time())
        while int(time.time()) <= start + self.timeout:
            response = rpc.get_response(self.endpoint_url)
            if self._is_valid_response(response):
                return response.json()

        return rpc.get_response(self.url)


class ETBExecutionRPC(object):
    """
    Wrapper around the etb-config that allows you to make batch requests or
    requests to one specific client.
    """

    def __init__(self, etb_config, non_error=True, timeout=5, protocol="http"):
        self.etb_config = etb_config
        self.non_error = non_error
        self.timeout = timeout
        self.protocol = protocol

        if protocol not in ["http", "ws"]:
            raise Exception("non-implemented protocol for ExecutionRPC connection")

        self._get_all_execution_endpoints()

    def _get_all_execution_endpoints(self):
        self.execution_endpoints = {}
        for name, ec in self.etb_config.get("execution-clients").items():
            for node in range(ec.get("num-nodes")):
                ip = ec.get("ip-addr", node)
                port = ec.get(f"execution-{self.protocol}-port")
                url = f"{self.protocol}://{ip}:{port}"
                self.execution_endpoints[f"{name}-{node}"] = ExecutionJSONRPC(
                    url, self.non_error, self.timeout
                )

        for name, cc in self.etb_config.get("consensus-clients").items():
            if cc.has_local_exectuion_client:
                for node in range(cc.get("num-nodes")):
                    ip = cc.get("ip-addr", node)
                    port = cc.get(f"execution-{self.protocol}-port")
                    url = f"{self.protocol}://{ip}:{port}"
                    self.execution_endpoints[f"{name}-{node}"] = ExecutionJSONRPC(
                        url, self.non_error, self.timeout
                    )

    def get_client_nodes(self):
        return self.execution_endpoints.keys()

    def do_rpc_request(self, rpc_method, client_nodes=[None], all_clients=False):
        if all_clients:
            ep = self.get_client_nodes()
        else:
            if not isinstance(client_nodes, list):
                ep = [client_nodes]
            else:
                ep = client_nodes

        all_responses = {}
        for name, ejr in self.execution_endpoints.items():
            if name in ep:
                all_responses[name] = ejr.send_payload(rpc_method)

        if len(all_responses.keys()) == 0:
            raise Exception(
                "Bad client_nodes: {client_nodes} need one of {self.get_client_nodes()}"
            )

        return all_responses
