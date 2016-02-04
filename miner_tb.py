from sys import argv

from sugarfree import *

cpu = SugarFreeCore()
cpu.trace_file = open('trace.txt', 'w+')
cpu.verbose = False
filename = argv[1]

# testbench resets core
cpu.cycle_count = 3

for addr, l in enumerate(open(filename + '_d.hex')):
    cpu.net_set_dmem(4 * addr, int(l, 16))

# fill in the rest of dmem with zeros for cycle accuracy
for addr in range(addr + 1, 1024):
    cpu.net_set_dmem(4 * addr, 0)

# testbench clears out memory yumi/valid
cpu.cycle_count += 2

for addr, l in enumerate(open(filename + '_i.hex')):
    cpu.net_set_imem(addr, int(l, 16))

for addr in range(addr + 1, 1024):
    cpu.net_set_imem(addr, 0)

for l in open(filename + '_r.hex'):
    cpu.net_set_reg(int(l[:2], 16), int(l[2:], 16))

for i, v in enumerate([0x56f6950a, 0x86a3a529, 0x7961969c, 0x7bfdb28c,
                       0x54c9af5a, 0x951237b8, 0x7979d96f, 0xc01823e1,
                       0xa24c2683, 0xcf1beb52, 0x2cf50119]):
    cpu.net_set_reg(i + 1, v)

# LOAD_WORK
cpu.net_set_reg(20, 1)
cpu.net_set_pc(0)

try:
    while 1:
        cpu.step_once()
except Wait:
    assert cpu.barrier == 0

nonce = 0
while 1:
    try:
        # match cycle behavior of testbench
        cpu.cycle_count += 2

        # LOAD_NONCE
        cpu.net_set_reg(20, 2)
        cpu.net_set_reg(1, nonce)
        cpu.net_set_pc(0)

        while 1:
            cpu.step_once()
    except Wait:
        if cpu.barrier == 0:
            print
            print "New nonce", nonce
            nonce += 1
        else:
            print
            print "Found!", nonce
            assert nonce == 8
            break

cpu.cycle_count += 2
cpu.net_set_reg(20, 3)
cpu.net_set_pc(0)

try:
    while 1:
        cpu.step_once()
except GOODBEEF:
    print "Stopping successfully"
    # The instruction count is off by one since we interrupted
    print cpu.cycle_count, "cycles", cpu.inst_count - 1, "instructions"
