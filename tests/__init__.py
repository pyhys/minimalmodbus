#!/usr/bin/env python
#
#   Copyright 2015 Jonas Berg
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

"""
.. moduleauthor:: Jonas Berg <pyhys@users.sourceforge.net>

"""

__author__  = "Jonas Berg"
__email__   = "pyhys@users.sourceforge.net"
__license__ = "Apache License, Version 2.0"

import unittest

import tests.test_minimalmodbus
import tests.test_eurotherm3500
import tests.test_omegacn7500

def suite_all_simulated():
    suite = unittest.TestLoader().loadTestsFromModule( test_minimalmodbus )
    suite.addTest( unittest.TestLoader().loadTestsFromModule(test_eurotherm3500) )
    suite.addTest( unittest.TestLoader().loadTestsFromModule(test_omegacn7500) )
    return suite
    
