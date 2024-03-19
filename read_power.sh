#!/bin/bash

read_dev() {
    echo $1 > /dev/usbtmc$2
    echo "$(head -n1 /dev/usbtmc$2),"
}

for i in {0..1}; do
    dev_str=$(read_dev "*IDN?" $i)
    for c in {1..3}; do
        dev_str+=$(read_dev ":MEASure:ALL? CH$c" $i)
    done
    echo $dev_str
done
