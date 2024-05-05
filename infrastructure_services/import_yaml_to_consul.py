import yaml
import consul


def import_to_consul(config, consul_client, prefix=""):
    for key, value in config.items():
        full_key = f"{prefix}/{key}" if prefix else key

        if isinstance(value, dict):
            import_to_consul(value, consul_client, prefix=full_key)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                import_to_consul(item, consul_client, prefix=full_key)
        else:
            consul_client.kv.put(full_key, str(value))


def main():
    with open("./consul-config/config.yaml", "r") as yaml_file:
        config = yaml.safe_load(yaml_file)

    consul_client = consul.Consul()
    import_to_consul(config, consul_client)

    print("Config imported to Consul successfully.")


if __name__ == "__main__":
    main()
