#include <stdint.h>

extern int main(void);

void Default_Handler(void)
{
    for (;;) { }
}

void Reset_Handler(void);

/* Each exception handler is a weak alias for Default_Handler. An exercise that
   needs one -- SysTick for a periodic interrupt, say -- defines a function of
   the same name in its own source file, and the linker prefers that over the
   weak symbol. Nothing in this file has to be edited.

   That matters more than it sounds. When the table was a flat list of
   Default_Handler, an exercise that forgot to wire up its handler still built
   and still ran: the interrupt simply went to an empty loop, the firmware did
   nothing, and no diagnostic was produced anywhere. */
#define WEAK_HANDLER __attribute__((weak, alias("Default_Handler")))

void NMI_Handler(void)        WEAK_HANDLER;
void HardFault_Handler(void)  WEAK_HANDLER;
void MemManage_Handler(void)  WEAK_HANDLER;
void BusFault_Handler(void)   WEAK_HANDLER;
void UsageFault_Handler(void) WEAK_HANDLER;
void SVC_Handler(void)        WEAK_HANDLER;
void DebugMon_Handler(void)   WEAK_HANDLER;
void PendSV_Handler(void)     WEAK_HANDLER;
void SysTick_Handler(void)    WEAK_HANDLER;

__attribute__((used, section(".isr_vector"), aligned(8)))
void (*const g_pfnVectors[])(void) = {
    (void (*)(void))0x20080000,   /*  0  initial stack pointer */
    Reset_Handler,                /*  1 */
    NMI_Handler,                  /*  2 */
    HardFault_Handler,            /*  3 */
    MemManage_Handler,            /*  4 */
    BusFault_Handler,             /*  5 */
    UsageFault_Handler,           /*  6 */
    (void (*)(void))0,            /*  7  reserved */
    (void (*)(void))0,            /*  8  reserved */
    (void (*)(void))0,            /*  9  reserved */
    (void (*)(void))0,            /* 10  reserved */
    SVC_Handler,                  /* 11 */
    DebugMon_Handler,             /* 12 */
    (void (*)(void))0,            /* 13  reserved */
    PendSV_Handler,               /* 14 */
    SysTick_Handler,              /* 15 */
};

extern uint32_t _sdata;
extern uint32_t _edata;
extern uint32_t _sbss;
extern uint32_t _ebss;
extern uint32_t _data_load;

void Reset_Handler(void)
{
    uint32_t *src = &_data_load;
    uint32_t *dst = &_sdata;

    while (dst < &_edata) {
        *dst++ = *src++;
    }

    dst = &_sbss;
    while (dst < &_ebss) {
        *dst++ = 0;
    }

    main();

    for (;;) { }
}
