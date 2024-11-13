#!/usr/bin/env python
# SPDX-FileCopyrightText: 2022 Leroy Hopson <copyright@leroy.nix.nz>
#
# SPDX-License-Identifier: CC0-1.0

# Usage: rebalance.py current_world current_nz current_vn new_amount

import sys

current_world = float(sys.argv[1])
current_nz = float(sys.argv[2])
current_vn = float(sys.argv[3])
new_amount = float(sys.argv[4])

new_total = current_world + current_nz + current_vn + new_amount

expected_world = new_total * 0.74
expected_nz = new_total * 0.19
expected_vn = new_total * 0.07

new_world = expected_world - current_world
new_nz = expected_nz - current_nz
new_vn = expected_vn - current_vn
print("### TO EACH ###")
print("World", round(new_world, 2))
print("NZ   ", round(new_nz, 2))
print("VN   ", round(new_vn, 2))

new_total = round(current_world + current_nz + new_amount, 2)

new_world = new_total * (74/93) - current_world
new_nz = new_total * (19/93) - current_nz
print("\n### World/NZ ONLY ###")
print("World", round(new_world, 2), "{}%".format(round(new_world / new_amount * 100, 2)))
print("NZ   ", round(new_nz, 2), "{}%".format(round(new_nz / new_amount * 100, 2)))

