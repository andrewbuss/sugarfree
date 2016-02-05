from collections import defaultdict
from sys import argv

from sugarfree import *

cpu = SugarFreeCore()
tracefile = None

if len(argv) > 2:
    tracefile = open(argv[2])
if len(argv) > 1:
    kernel_path = argv[1]
elif len(argv) == 0:
    print "Need an assembled kernel path to disassemble"
    print "e.g. core/src/tb/miner_tb/miner (omit suffixes)"

rf = defaultdict(int)
for l in open(kernel_path + '_r.hex'):
    rf[int(l[:2], 16)] = int(l[2:], 16)

totals = defaultdict(int)
if tracefile:
    for l in tracefile:
        cycle, instr, pc, rs, rd = map(int, l.split())
        if pc not in totals:
            totals[pc] = 0
        totals[pc] += 1

for addr, l in enumerate(open(kernel_path + '_i.hex')):
    instr = Instruction.decode(int(l, 16))
    instr.rd_str = reg_str(instr.rd, rf[instr.rd])
    instr.rs_str = reg_str(instr.rs, rf[instr.rs])
    if tracefile:
        print '%6d %04x:\t%s' % (totals[addr], addr, str(instr).replace(' ', '\t'))
    else:
        print '%04x:\t%s' % (addr, str(instr).replace(' ', '\t'))