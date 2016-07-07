#!/bin/bash

testprog="hbserve"
#testprog="testbench"

if [ "$testprog" == "hbserve" ]
then
   url="http://127.0.0.1:9090/"
else
   url="http://127.0.0.1:8000/"
fi

#http --form -v POST $url testdate="2016-05-01T05:50" phone=9872882112 description=description name="Sandeep Nangia" email="sandeep.nangia@gmail.com" file@allah.pdf

http --form -v POST $url testdate="2016-05-01T05:50" phone=919872882112 description="description 1" name="Sandeep Nangia" email="sandeep.nangia@gmail.com" file@allah.pdf sid="sid1" pid="pid1"

#http --form -v POST $url testdate="2016-05-01T05:50" phone=919872882112 description="description 1" name="Sandeep Nangia" email="sandeep.nangia@gmail.com" file@allah.pdf
#http --form -v POST $url testdate="2016-05-01T05:50" phone=919872882112 description="description 2" name="Sandeep Nangia" email="sandeep.nangia@gmail.com" file@allah.pdf

#http --form -v POST $url testdate="2016-05-01T05:50" phone=919872882112 description="description 3" name="Sandeep Nangia" email="sandeep.nangia@gmail.com" file@allah.pdf

#http --form -v POST $url testdate="2016-05-01T05:50" phone=919872882112 description="description 4" name="Sandeep Nangia" email="sandeep.nangia@gmail.com" file@allah.pdf

#http --form -v POST $url testdate="2016-05-01T05:50" phone=919872882112 description="description 5" name="Sandeep Nangia" email="sandeep.nangia@gmail.com" file@allah.pdf
