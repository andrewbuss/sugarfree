from sys import argv

from sugarfree import *

cpu = SugarFreeCore()

filename = argv[1]

for addr, l in enumerate(open(filename + '_i.hex')):
    cpu.net_set_imem(addr, int(l, 16))

for addr, l in enumerate(open(filename + '_d.hex')):
    cpu.net_set_dmem(4 * addr, int(l, 16))

for l in open(filename + '_r.hex'):
    cpu.net_set_reg(int(l[:2], 16), int(l[2:], 16))

try:
    while 1:
        cpu.step_once()
except Wait:
    assert cpu.barrier == 0
except GOODBEEF:
    print "Stopping successfully"
    print cpu.cycle_count, "cycles", cpu.inst_count, "instructions"
