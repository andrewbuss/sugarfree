from sys import stderr

signed = lambda x, bits: x if x < (1 << (bits - 1)) else x - (1 << bits)
unsigned = lambda x, bits: x if x >= 0 else (1 << bits) + x
reg_str = lambda r, v: '%#x' % v if r > 0x20 else '$R%d' % r


class Instruction(object):
    rd, rs, offset6, offset11 = 0, 0, 0, 0
    rd_str, rs_str = '', ''
    opcode_map = {}

    @classmethod
    def register(cls, opcode, instr):
        cls.opcode_map[opcode] = instr
        return instr

    @classmethod
    def decode(cls, instr):
        opcode = instr >> 11
        rd, rs = (instr >> 6) & 0x1F, instr & 0x3F
        decoded = cls.opcode_map[opcode]()
        decoded.rd, decoded.rs = rd, rs
        decoded.offset11 = instr & 0x7FF
        decoded.offset6 = signed(instr & 0x3F, 6)
        return decoded

    def update_pc(self, cpu):
        cpu.pc += 1

    def execute(self, cpu):
        pass

    def __str__(self):
        return '%s %s, %s' % (self.__class__.__name__, self.rd_str, self.rs_str)


class Branch(Instruction):
    next_pc = None

    def update_pc(self, cpu):
        cpu.pc = self.next_pc if self.next_pc else cpu.pc + 1


class Conditional(Branch):
    def take_branch(self, cpu):
        return False

    def execute(self, cpu):
        self.next_pc = cpu.pc + self.offset6 if self.take_branch(cpu) else None

    def __str__(self):
        return '%s %s, %d' % (self.__class__.__name__, self.rd_str, self.offset6)


def register_opcode(opcode):
    return lambda cls: Instruction.register(opcode, cls)


@register_opcode(0)
class ADDU(Instruction):
    def execute(self, cpu):
        cpu.rf[self.rd] = (cpu.rd_val + cpu.rs_val) & 0xFFFFFFFF


@register_opcode(1)
class SUBU(Instruction):
    def execute(self, cpu):
        cpu.rf[self.rd] = unsigned((cpu.rd_val - cpu.rs_val) & 0xFFFFFFFF, 32)


@register_opcode(0x2)
class SLLV(Instruction):
    def execute(self, cpu):
        cpu.rf[self.rd] <<= (cpu.rs_val & 0x1F)
        cpu.rf[self.rd] &= 0xFFFFFFFF


@register_opcode(0x3)
class SRAV(Instruction):
    def execute(self, cpu):
        cpu.rf[self.rd] >>= (cpu.rs_val & 0x1F)
        cpu.rf[self.rd] |= (1 << (cpu.rs_val + 1) - 1) << (31 - cpu.rs_val)


@register_opcode(0x4)
class SRLV(Instruction):
    def execute(self, cpu):
        cpu.rf[self.rd] >>= (cpu.rs_val & 0x1F)


@register_opcode(0x5)
class AND(Instruction):
    def execute(self, cpu):
        cpu.rf[self.rd] = cpu.rd_val & cpu.rs_val


@register_opcode(0x6)
class OR(Instruction):
    def execute(self, cpu):
        cpu.rf[self.rd] = cpu.rd_val | cpu.rs_val


@register_opcode(0x7)
class NOR(Instruction):
    def execute(self, cpu):
        cpu.rf[self.rd] = ~(cpu.rd_val | cpu.rs_val) & 0xFFFFFFFF


@register_opcode(0x8)
class SLT(Instruction):
    def execute(self, cpu):
        cpu.rf[self.rd] = 1 if (cpu.rd_val_signed < cpu.rs_val_signed) else 0


@register_opcode(0x9)
class SLTU(Instruction):
    def execute(self, cpu):
        cpu.rf[self.rd] = 1 if (cpu.rd_val < cpu.rs_val) else 0


@register_opcode(0xA)
class MOV(Instruction):
    def execute(self, cpu):
        cpu.rf[self.rd] = cpu.rs_val


@register_opcode(0x10)
class BEQZ(Conditional):
    def take_branch(self, cpu):
        return cpu.rd_val == 0


@register_opcode(0x11)
class BNEQZ(Conditional):
    def take_branch(self, cpu):
        return cpu.rd_val != 0


@register_opcode(0x12)
class BGTZ(Conditional):
    def take_branch(self, cpu):
        return not (cpu.rd_val & (1 << 31))


@register_opcode(0x13)
class BLTZ(Conditional):
    def take_branch(self, cpu):
        return cpu.rd_val & (1 << 31)


@register_opcode(0x16)
class JAL(Branch):
    def execute(self, cpu):
        self.next_pc = cpu.rs_val
        cpu.rf[self.rd] = cpu.pc + 1

    def __str__(self):
        return '%s %s, %s' % (self.__class__.__name__, self.rd_str, self.rs_str)


@register_opcode(0x17)
class JALR(Branch):
    def execute(self, cpu):
        self.next_pc = cpu.rs_val
        cpu.rf[self.rd] = cpu.pc + 1

    def __str__(self):
        return '%s %s, %s' % (self.__class__.__name__, self.rd_str, self.rs_str)


@register_opcode(0x18)
class LW(Instruction):
    def execute(self, cpu):
        cpu.rf[self.rd] = cpu.read_mem(cpu.rs_val)


@register_opcode(0x19)
class LBU(Instruction):
    def execute(self, cpu):
        cpu.rf[self.rd] = cpu.read_mem(cpu.rs_val, byte=True)


@register_opcode(0x1A)
class SW(Instruction):
    def execute(self, cpu):
        cpu.write_mem(cpu.rd_val, cpu.rs_val)


@register_opcode(0x1B)
class SBU(Instruction):
    def execute(self, cpu):
        cpu.write_mem(cpu.rd_val, cpu.rs_val, byte=True)


@register_opcode(0x1C)
class LG(Instruction):
    def execute(self, cpu):
        cpu.rf[1] = cpu.read_mem(self.offset11)

    def __str__(self):
        return '%s %#3x' % (self.__class__.__name__, self.offset11)


class Wait(Exception):
    pass


@register_opcode(0xC)
class WAIT(Instruction):
    def execute(self, cpu):
        raise Wait

    def __str__(self):
        return '%s' % self.__class__.__name__


@register_opcode(0xD)
class BAR(Instruction):
    def execute(self, cpu):
        cpu.barrier = cpu.rs_val

    def __str__(self):
        return '%s %s' % (self.__class__.__name__, self.rs_str)


class DEADDEAD(Exception):
    pass


class GOODBEEF(Exception):
    pass


class SugarFreeCore(object):
    def __init__(self):
        self.barrier = 0
        self.inst_count = 0
        self.cycle_count = 0
        self.pc = 0
        self.rf = [0 for _ in range(0x40)]
        self.imem = [0 for _ in range(0x400)]
        self.trace_file = None
        self.verbose = False
        self.check_addr = lambda x: x
        self.dmem = [0 for _ in range(0x400)]

    def step_once(self):
        self.rf[0] = 0
        instr = Instruction.decode(self.imem[self.pc])
        self.cycle_count += 1
        self.rd_val, self.rs_val = self.rf[instr.rd], self.rf[instr.rs]
        self.rd_val_signed = signed(self.rf[instr.rd], 32)
        self.rs_val_signed = signed(self.rf[instr.rs], 32)
        instr.rd_str = reg_str(instr.rd, self.rd_val)
        instr.rs_str = reg_str(instr.rs, self.rs_val)
        if self.verbose:
            print '%8d' % self.cycle_count, '%04x' % self.pc, str(instr).replace(' ', '\t')

        # for comparison with provided testbench

        try:
            instr.execute(self)
            if self.trace_file:
                self.trace_file.write("%d %d %d %d %d\n" % (
                    self.cycle_count, self.inst_count, self.pc, self.rs_val, self.rd_val))
            instr.update_pc(self)
        finally:
            self.inst_count += 1

    def net_set_reg(self, r, v):
        self.cycle_count += 1
        self.rf[r] = v

    def net_set_pc(self, pc):
        self.cycle_count += 1
        self.pc = pc

    def net_set_dmem(self, addr, val):
        self.cycle_count += 1
        self.write_mem(addr, val)

    def net_set_imem(self, addr, val):
        self.cycle_count += 1
        self.imem[addr] = val

    # default testbench memory behavior
    def read_mem(self, addr, byte=False):
        self.cycle_count += 1
        addr, shift = addr / 4, 24 - (3 - addr % 4) * 8
        assert addr < len(self.dmem)
        if byte:
            return (self.dmem[addr] >> shift) & 0xFF
        else:
            return self.dmem[addr]

    def write_mem(self, addr, val, byte=False):
        self.cycle_count += 1
        if addr == 0xDEADDEAD:
            raise DEADDEAD
        elif addr == 0xC0DEC0DE:
            print >> stderr, 'CODE %08x' % val
        elif addr == 0xC0FFEEEE:
            print >> stderr, 'PASS %08x' % val
        elif addr == 0x600DBEEF:
            print >> stderr, 'DONE'
            raise GOODBEEF
        else:
            addr, shift = addr / 4, 24 - (3 - addr % 4) * 8
            assert addr <= len(self.dmem)
            if byte:
                old_val = self.dmem[addr] & ~(0xFF << shift)
                self.dmem[addr] = old_val | (val << shift)
            else:
                self.dmem[addr] = val
