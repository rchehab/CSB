#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

set -e


#options="24 25 26 27"
options="24"

for a in $options
do
	echo $a | ./run.sh
done
