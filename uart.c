#include <stdint.h>

#define SCI0_BASE 0x40118000UL

/* Module Stop Control Register B.
 *
 * On the RA6M5 every peripheral leaves reset with its clock stopped, and
 * writes to a stopped module's registers do not take effect. A module's bit
 * must be cleared before any of its registers are touched. The reset value is
 * all ones, so everything starts stopped.
 *
 * Without this, uart_init appears to succeed, TE is never really set, and
 * uart_putc spins forever on a TDRE flag that can never become set.
 *
 * Renode does not model module-stop control -- its platform description only
 * tags this address, so writes are absorbed and ignored. The simulator
 * therefore transmits with or without this line, and CI cannot tell the
 * difference. It matters on real silicon.
 *
 * MSTPB_SCI0 follows the RA-family convention and has not been confirmed
 * against the RA6M5 hardware manual. Check it before relying on this on
 * hardware. If the bit is wrong, SCI0 stays stopped exactly as it does today
 * and an unrelated module gets clocked -- no new failure mode is introduced.
 */
#define MSTPCRB    (*(volatile uint32_t *)0x40084004UL)
#define MSTPB_SCI0 (1u << 31)

#define SCI_SMR (*(volatile uint8_t *)(SCI0_BASE + 0x00))
#define SCI_BRR (*(volatile uint8_t *)(SCI0_BASE + 0x01))
#define SCI_SCR (*(volatile uint8_t *)(SCI0_BASE + 0x02))
#define SCI_TDR (*(volatile uint8_t *)(SCI0_BASE + 0x03))
#define SCI_SSR (*(volatile uint8_t *)(SCI0_BASE + 0x04))

#define SCR_RE   (1u << 4)
#define SCR_TE   (1u << 5)
#define SSR_TDRE (1u << 7)

void uart_init(void)
{
    MSTPCRB &= ~MSTPB_SCI0;

    SCI_SCR = 0;
    SCI_SMR = 0;
    SCI_BRR = 216;
    SCI_SCR = SCR_RE | SCR_TE;
}

void uart_putc(char c)
{
    while (!(SCI_SSR & SSR_TDRE)) { }
    SCI_TDR = (uint8_t)c;
}

void uart_puts(const char *s)
{
    while (*s) {
        uart_putc(*s++);
    }
}
