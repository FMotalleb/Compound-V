import yaml


def readConfig():
    with open("config.yaml", "r") as yamlfile:
        return yaml.load(yamlfile, Loader=yaml.FullLoader)


def saveConfig(name, config):
    output = readConfig()
    output['configs'][name] = config
    with open("config.yaml", "w") as yamlfile:
        return yaml.dump(output, yamlfile)
