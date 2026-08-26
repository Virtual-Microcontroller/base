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
the firmware **says something** on the UART. It does not care what. Change
what `main.c` prints as often as you like; the check keeps passing.

What it catches is silence: firmware that compiles cleanly and produces no
output at all. That is a real bug and an easy one to write - a `main()` that
never reaches your `uart_puts`, or a status-flag loop that spins forever
because the register is not `volatile`. Without this check you would only
find out when you pressed Run and the terminal stayed empty.

If an assignment must print exact text, add the string to the `test` target:

```make
test: app.elf
	$(PYTHON) tests/run_renode_test.py --elf app.elf --expected "Ready"
```

The same check runs in CI, so silent firmware fails there rather than
surprising you in the simulator.

## Push it

Every push builds your firmware, runs the simulator check, and uploads
`app.elf`. Watch it under the **Actions** tab, then open the course dashboard
and press **Run** to see your program's output.

## The AI teaching assistant

If your instructor enabled it, an AI assistant helps when things break.
**When a build fails**, it reads the error and writes hints into your code as
comment lines, then pushes them to your branch:

```c
/* AI-HINT: this loop reads a hardware register - what stops the compiler
   from caching it in a register instead of re-reading it? */
while (uart_busy()) { }
```

So the workflow is:

1. You push code that does not build.
2. Wait about a minute, then **`git pull`**.
3. The hints are now in your files, on the lines that need attention.
4. Fix the code and delete nothing — the markers are removed for you.
5. Push again.

When the build passes, the assistant reviews what you changed and comments on
your commit. GitHub emails that to you. It also clears the `AI-HINT` lines, so
your finished file is your own work with no leftovers.

**Pull before you start fixing.** If you edit without pulling, your push is
rejected because the assistant has already added a commit. If you would rather
not wait, fix it yourself and push — the assistant notices your branch has
moved on and stays out of the way.

It gives **hints, not answers** — working out the fix is the exercise. If the
same build keeps failing it gets more specific each time, and after several
attempts it will tell you to ask your instructor. It can only add and remove
its own comment lines; it cannot change a line of your code.

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
