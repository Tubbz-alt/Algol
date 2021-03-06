# See LICENSE for license details.

#*****************************************************************************
# illegal.S
#-----------------------------------------------------------------------------
#
# Test illegal instruction trap.
#

#include "riscv_test.h"
#include "test_macros.h"

RVTEST_RV64S
RVTEST_CODE_BEGIN

#ifdef __MACHINE_MODE
  #define sscratch mscratch
  #define sstatus mstatus
  #define scause mcause
  #define sepc mepc
  #define stvec_handler mtvec_handler
#endif

  li TESTNUM, 2
  .word 0
  j fail

  j pass

  TEST_PASSFAIL

stvec_handler:
  li t1, CAUSE_ILLEGAL_INSTRUCTION
  csrr t0, scause
  bne t0, t1, fail
  csrr t0, sepc
  addi t0, t0, 8
  csrw sepc, t0
  sret

RVTEST_CODE_END

  .data
RVTEST_DATA_BEGIN

  TEST_DATA

RVTEST_DATA_END
