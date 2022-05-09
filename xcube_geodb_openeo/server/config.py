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

from pathlib import Path
from typing import Dict, Any, Union

import yaml

from defaults import API_VERSION, STAC_VERSION, SERVER_URL, SERVER_ID, \
    SERVER_TITLE, SERVER_DESCRIPTION

Config = Dict[str, Any]


def load_config(config_path: Union[str, Path]) -> Config:
    with open(config_path, 'r') as fp:
        config = yaml.safe_load(fp)
        if 'API_VERSION' not in config:
            config['API_VERSION'] = API_VERSION
        if 'STAC_VERSION' not in config:
            config['STAC_VERSION'] = STAC_VERSION
        if 'SERVER_URL' not in config:
            config['SERVER_URL'] = SERVER_URL
        if 'SERVER_ID' not in config:
            config['SERVER_ID'] = SERVER_ID
        if 'SERVER_TITLE' not in config:
            config['SERVER_TITLE'] = SERVER_TITLE
        if 'SERVER_DESCRIPTION' not in config:
            config['SERVER_DESCRIPTION'] = SERVER_DESCRIPTION
        return config
