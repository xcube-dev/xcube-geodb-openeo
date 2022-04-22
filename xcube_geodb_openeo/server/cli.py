# The MIT License (MIT)
# Copyright (c) 2021/2022 by the xcube team and contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
from typing import Optional

import click

WEB_FRAMEWORK_TORNADO = 'tornado'
WEB_FRAMEWORK_FLASK = 'flask'
WEB_FRAMEWORKS = [WEB_FRAMEWORK_FLASK, WEB_FRAMEWORK_TORNADO]

DEFAULT_CONFIG_PATH = 'config.yml'
DEFAULT_WEB_FRAMEWORK = WEB_FRAMEWORK_FLASK
DEFAULT_ADDRESS = '0.0.0.0'
DEFAULT_PORT = 5000


@click.command()
@click.option('--config', '-c', 'config_path', default=DEFAULT_CONFIG_PATH,
              help='Path to configuration YAML file.')
@click.option('--address', '-a', default=DEFAULT_ADDRESS,
              help='Server address.')
@click.option('--port', '-p', default=DEFAULT_PORT,
              help='Server port number.')
@click.option('--framework', '-f',
              help='Web framework to be used.',
              default=DEFAULT_WEB_FRAMEWORK,
              type=click.Choice(WEB_FRAMEWORKS))
@click.option('--debug', '-d', is_flag=True,
              help='Turn debug mode on.')
@click.option('--verbose', '-v', is_flag=True,
              help='Turn verbose mode on.')
def main(config_path: Optional[str],
         address: str = DEFAULT_ADDRESS,
         port: int = DEFAULT_PORT,
         framework: str = DEFAULT_WEB_FRAMEWORK,
         debug: bool = False,
         verbose: bool = False):
    """
    A server that represents the openEO backend for the xcube geoDB.
    """
    import importlib
    from xcube_geodb_openeo.server.config import load_config

    config = load_config(config_path) if config_path else {}

    module = importlib.import_module(
        f'xcube_geodb_openeo.server.app.{framework}'
    )

    # noinspection PyUnresolvedReferences
    module.serve(config=config,
                 address=address,
                 port=port,
                 debug=debug,
                 verbose=verbose)


if __name__ == '__main__':
    main()
