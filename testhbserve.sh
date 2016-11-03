#!/bin/bash

testprog="hbserve"
#testprog="testbench"
url="http://127.0.0.1:9090/"

http --form -v POST $url testdate="2016-10-26T05:50" phone=919872882112 description="description 1" name="Sandeep Nangia" email="sandeep.nangia@gmail.com" file@allah.pdf sid="sid1" pid="pid1" labid="haematology"

