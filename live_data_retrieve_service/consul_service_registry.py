import consul


class ConsulServiceRegistry:
    def __init__(self, consul_host='localhost', consul_port=8500):
        self.consul = consul.Consul(host=consul_host, port=consul_port)
        self.service_id = None

    def register_service(self, service_name, service_address, service_port):
        check = consul.Check.http(f"http://{service_address}:{service_port}/health", "10s")
        self.service_id = f"{service_name}-{service_address}-{service_port}"
        self.consul.agent.service.register(
            name=service_name,
            service_id=self.service_id,
            address=service_address,
            port=service_port,
            check=check
        )

    def deregister_service(self):
        self.consul.agent.service.deregister(service_id=self.service_id)

    def get_service_addresses(self, service_name):
        result = []
        services = self.consul.agent.services()
        for _, service in services.items():
            if service['Service'] == service_name:
                result.append((service['Address'], service['Port']))
        return result

    def get_config(self, name):
        settings = self.consul.kv.get(name)
        if settings and settings[1]:
            return settings[1]['Value'].decode("utf-8")
        return None
