from avmon import config


def test_example_config_valid():
    config.load(dotenv=False)
