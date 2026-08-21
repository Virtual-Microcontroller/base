# CK-RA6M5 Starter Project

Bare-metal C for the Renesas CK-RA6M5 board (R7FA6M5B, ARM Cortex-M33).

Push your code and GitHub builds it, checks it in a simulator, and makes it
available in the course dashboard where you can watch its UART output live.

## What is here

| File | What it does |
| --- | --- |
| `main.c` | Entry point. Start here. |
| `uart.c` | SCI0 serial driver — how characters reach your screen |
| `startup.c` | Vector table and reset handler; runs before `main` |
| `link.ld` | Memory layout: flash at `0x00000000` (2M), RAM at `0x20000000` (512K) |
| `Makefile` | `make` to build, `make test` to check it in the simulator |
| `platform.json` | Which Renode board and UART peripheral to simulate |
| `tests/run_renode_test.py` | Loads the firmware in Renode and looks for expected UART output |

## Build it

You need `arm-none-eabi-gcc` (13.2) and GNU Make.

```bash
make
```

Produces `app.elf` (what the simulator runs) and `app.hex`.

## Test it

You need Renode on your `PATH`.

```bash
make test
```

Loads `app.elf` onto the board described by `platform.json` and checks that
`Hello world!` appears on the UART. The starter code passes. Once you change
what `main.c` prints, update the expected string in the `test` target of the
`Makefile` to match.

This same check runs in CI, so a build that compiles but produces no output
fails there rather than surprising you in the simulator.

## Push it

Every push builds your firmware, runs the simulator check, and uploads
`app.elf`. Watch it under the **Actions** tab, then open the course dashboard
and press **Run** to see your program's output.

## The AI teaching assistant

If your instructor enabled it, an AI assistant helps when things break.
**When a build fails**, it reads the error and opens an issue in this
repository with hints about what to look at.

It gives **hints, not answers** — working out the fix is the exercise. If the
same build keeps failing it gets more specific each time, and after several
attempts it will tell you to ask your instructor. It cannot change your code;
it can only comment.

## When the build fails

Read the **first** error in the Actions log. Later errors are usually knock-on
effects of the first.

This project compiles with `-Wall -Wextra -Werror`, so **any warning stops the
build**. An unused variable is a hard error here even though it would be
harmless elsewhere. That is deliberate: on a microcontroller, the warnings you
ignore are the bugs you chase later.

| Message | Usually means |
| --- | --- |
| `undefined reference to 'foo'` | The linker cannot find `foo`. Is its `.c` file listed in `SRCS` in the `Makefile`? |
| `implicit declaration of function 'foo'` | You called `foo` before declaring it. |
| `unused variable` / `unused parameter` | `-Werror` turning a warning into an error. |
| `region 'FLASH' overflowed` | Your program outgrew the memory budget in `link.ld`. |
| `undefined reference to 'printf'` (or `malloc`, `memcpy`) | There is no standard library here — `-nostdlib` means you write it or do without it. |
| `make test` fails but `make` works | It compiled, but the simulator never saw the text it expected. |

### The bug with no error message

If your program hangs while waiting on a hardware register, check that the
register is declared `volatile`. Without it the compiler may read the register
once and reuse that value forever, so a loop like

```c
while (!(SCI_SSR & SSR_TDRE)) { }
```

can spin forever at `-Os`. See how the registers in `uart.c` are declared.
This produces no warning at all, which is what makes it worth remembering.

## Using a different board

`platform.json` selects the simulated hardware:

```json
{
  "platform_repl": "platforms/boards/renesas-ck_ra6m5.repl",
  "uart_peripheral": "sysbus.sci0"
}
```

`platform_repl` may name a board that ships with Renode, or a `.repl` file you
commit to this repo. Both `make test` and the hosted simulator read this file,
so they always agree on what they are running.

## Learning more

- [Renode documentation](https://renode.readthedocs.io/)
- [CK-RA6M5 board page](https://www.renesas.com/en/design-resources/boards-kits/ck-ra6m5)
