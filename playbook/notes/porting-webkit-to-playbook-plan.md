# Porting WebKit to the BlackBerry PlayBook

Oct 4, 2026 · @Steve

> Local copy of the Claude Doc https://claude.ai/code/artifact/51e7a4fb-47a5-4a09-9014-90c82a42c519 (original link: https://claude.ai/artifact/B7cNF91FJCy1nnSSP16Xon). Written before the PlayBook was rooted; the simulator and signing sections are superseded by [playbook-webkit-port-handoff.md](playbook-webkit-port-handoff.md). The roadmap diagram in the "Phased plan" section is not included in this copy.

## Goal and scope

Build a native browser app for the BlackBerry PlayBook (Tablet OS 2.x) on a much newer WebKit than the stock browser, developed mostly on a laptop with the PlayBook simulator.

- **What we build:** a new app that sits beside the stock browser. We don't replace or patch RIM's closed-source browser.
- **Why WebKit:** RIM's QNX platform code for WebKit was open source and upstream until around 2013, so the hardest device-specific plumbing (graphics, input, networking, windowing) already existed once. Chromium needs a brand new QNX port. Firefox also needs a Rust compiler for ARMv7 QNX 6.x, which doesn't exist. NetSurf is the easy fallback but can't handle much of the modern web.
- **Engine vs shell:** WebKit is the engine. We wrap it first in a bare-bones shell (MiniBrowser: address bar, back, forward, reload), then grow that into a consumer-style browser with tabs, bookmarks and history.
- **Success, stage 1:** MiniBrowser loads a current HTTPS site with modern JavaScript in the simulator.
- **Success, stage 2:** the same build runs acceptably on a real PlayBook.

## Target platform

The PlayBook is a capable ARMv7 tablet on an old QNX userland; the toolchain, not the hardware, is the main constraint. Hardware figures below are from memory, not a fetched spec sheet.

| Item | PlayBook (approximate) | What it means for the port |
| --- | --- | --- |
| CPU | TI OMAP4430, dual Cortex-A9 at 1 GHz, NEON | Modern ARMv7 code paths and JIT targets still apply |
| RAM | 1 GB | Enough for a single-process engine; tight with many tabs |
| GPU | PowerVR SGX540, OpenGL ES 2.0 | Accelerated compositing works; no ES 3.0 features |
| Screen | 7 inch, 1024 x 600 | Touch-first shell UI |
| OS | BlackBerry Tablet OS 2.1, on QNX Neutrino 6.5 | POSIX, but an old libc and kernel APIs |
| Last Native SDK | 2.1.0.1032 ([ofxQNX notes](https://github.com/falcon4ever/ofxQNX)) | Ships an old GCC 4.x, far short of C++20 |
| UI frameworks | Native C/C++, Qt 4.x community builds, OpenGL ES ([Habr Qt guide](https://habr.com/ru/articles/138379/)) | Shell can be plain Qt or raw Screen + GL |

- **Open question:** exact GCC version in Native SDK 2.1. Confirm once the SDK is installed.
- **Open question:** exact QNX libc version, which decides how much C++20 library support needs shims.

## Development environment

Yes, this can start on the laptop: the PlayBook simulator is a VMware virtual machine, and the simulator doesn't require code signing. The catch is that the official download pages are gone, so the SDK and simulator have to come from archives.

**What the old setup looked like.** Developers installed the Native SDK (QNX Momentics IDE plus command-line tools), then VMware Player on Windows or Linux (Fusion on a Mac), then the PlayBook simulator image ([Game Developer setup guide](https://www.gamedeveloper.com/programming/playbook-development-setup); [Pete Freitag](https://www.petefreitag.com/blog/getting-started-with/)). Apps went onto the simulator with `blackberry-deploy -installApp -device <simulator IP> -package <file.bar>` with development mode on ([CrackBerry thread](https://forums.crackberry.com/blackberry-playbook-f222/list-playbook-applications-543531/)). The early simulator's development mode password was simply `password`.

**Suggested split of work:**

- **Laptop (Dell Inspiron 14):** runs VMware and the simulator, the shell app, and quick test cycles.
- **PowerEdge T640 (a Linux VM):** does the heavy WebKit compiles. A full WebKit build takes hours of sustained CPU, and the Inspiron already has a heat-related keyboard issue, so long builds there are a bad idea.

**Things to collect:**

- [ ] BlackBerry Native SDK 2.1 for Linux (and Windows, for the IDE) from archive.org or community mirrors
- [ ] PlayBook Tablet OS simulator 2.1 VMware image
- [ ] A current VMware Workstation or Player install on the laptop
- [ ] The `blackberry-deploy` and packaging tools (part of the SDK)

**The x86 catch.** The simulator runs x86 QNX, not ARM, and draws through VMware graphics instead of the PowerVR GPU. Every simulator milestone is therefore an x86 build, and the ARM build plus GPU paths get proven later on hardware.

- **Open question:** whether the 2.1 simulator image still boots on current VMware without tweaks to its virtual hardware settings.

## Phased plan

Phases 0 to 3 run entirely in the simulator on the laptop; only Phase 4 needs a real PlayBook.

*(Roadmap diagram: porting roadmap · 6 phases, 5 gates — not included in this copy.)*

1. **Collect the tools.** Install the Native SDK and simulator, then build and deploy one of the SDK's sample apps with `blackberry-deploy` to prove the pipeline.
2. **Build RIM's WebKit as-is.** Build the [WebKit-PlayBook](https://github.com/blackberry/WebKit-PlayBook) branch `playbook-2.1.0` with SDK 2.1 for the x86 simulator, inside a tiny shell (address bar, back, forward, reload). This proves building, packaging and deploying with code that is known to have worked, before anything changes.
3. **Modern toolchain.** On the T640, build a current Clang and libc++ cross toolchain using the SDK's QNX headers and libraries as the sysroot. Add a small shim library for missing libc functions as they turn up.
4. **Forward-port.** BlackBerry also published newer [BB10 WebKit](https://lists.webkit.org/pipermail/webkit-dev/2014-January/026039.html) source for the same QNX family, and the port lived in upstream WebKit until its [removal in January 2014](https://trac.webkit.org/r161661). Both make natural waypoints. Past 2014, the platform layer gets carried forward by hand between tagged releases.
5. **Real hardware.** Rebuild for ARMv7, switch to the PowerVR GPU paths, and tune memory. See the next section before buying a device.
6. **Consumer shell.** Grow the shell in Qt 4.x or raw Screen plus OpenGL ES: tabs, bookmarks, history, downloads.

## Deploying to a real PlayBook

Getting onto real hardware is the least certain part of the plan, because BlackBerry shut down the PlayBook's support infrastructure on January 4, 2022 ([r/blackberry summary](https://reddit.fabiomanganiello.com/r/blackberry/comments/irlvzo/blackberry_10pbos_infrastructure_eol)).

- **Signing:** on a real device, unsigned apps ran only with a debug token installed, and creating one required signing keys from BlackBerry ([Slashdot discussion](https://developers.slashdot.org/story/11/07/12/1939238/BlackBerry-Code-Signing-Server-Outage)). Those servers are part of the retired infrastructure.
- **Activation:** the same shutdown ended the services used to activate or factory reset a PlayBook. A wiped device may not get through setup.
- **Sideloading itself survived:** RIM limited consumer sideloading in OS 2.1 but kept developer sideloading through debug tokens ([IT World Canada](https://itworldcanada.com/?p=46190)).

**Buying advice:** get a PlayBook already set up on OS 2.1, and never factory reset it. Look for a seller who can show the home screen.

- **Open question:** whether a community method still produces working debug tokens, or re-signs .bar files, for PlayBook OS 2.1. Check CrackBerry and archived tools before buying.
- **Open question:** whether an existing debug token on a used unit still works past its expiry date.

## Risks and fallbacks

The biggest risk is the toolchain: if a modern Clang can't target QNX 6.5 cleanly, everything after Phase 1 stalls.

| Risk | Why it matters | Fallback |
| --- | --- | --- |
| No modern C++ toolchain for QNX 6.5 | Current WebKit needs C++20; the SDK ships GCC 4.x | Stop forward-porting at the newest WebKit the toolchain can build |
| QNX libc gaps | Modern libc++ and WebKit expect newer POSIX and threading APIs | A compatibility shim library, grown one missing function at a time |
| SDK or simulator unobtainable | No archive copy means no laptop development | Ask on CrackBerry; buy a device and test on hardware only |
| No way to sign for a real device | Port works only in the simulator | Simulator remains a useful proof; hunt for community signing tools |
| 1 GB RAM too tight | Modern sites may crash or swap | Single process, small caches, JIT tuned down |
| Rebasing years of WebKit history | 2012 to now is a huge gap | Jump in large steps between known-good tags, not commit by commit |

**Fallback options if the native port stalls:**

- **Remote rendering:** run Chromium on the T640 and stream pages to the stock browser or a thin client. Full modern web, no engine port.
- **NetSurf:** portable C, likely builds with the old GCC. Limited JavaScript and CSS, but a finished native browser.

## Sources

- [blackberry/WebKit-PlayBook](https://github.com/blackberry/WebKit-PlayBook): RIM's PlayBook WebKit source, branch playbook-2.1.0, archived 2019
- [Eli Fidler on webkit-dev, Jan 2014](https://lists.webkit.org/pipermail/webkit-dev/2014-January/026039.html): links to the PlayBook, BB10 and BBOS downstream WebKit repos
- [WebKit bug 126715](https://bugs.webkit.org/show_bug.cgi?id=126715) and [changeset r161661](https://trac.webkit.org/r161661): removal of the BlackBerry port from trunk, Jan 2014
- [ofxQNX](https://github.com/falcon4ever/ofxQNX): confirms Native SDK 2.1.0.1032 as the PlayBook SDK in use
- [Habr: Qt on PlayBook](https://habr.com/ru/articles/138379/): Native SDK, simulator and Qt build notes
- [Game Developer: PlayBook development setup](https://www.gamedeveloper.com/programming/playbook-development-setup)
- [Pete Freitag: getting started](https://www.petefreitag.com/blog/getting-started-with/)
- [CrackBerry: deploying .bar files](https://forums.crackberry.com/blackberry-playbook-f222/list-playbook-applications-543531/)
- [IT World Canada: PlayBook sideloading](https://itworldcanada.com/?p=46190)
- [Slashdot: code signing and debug tokens](https://developers.slashdot.org/story/11/07/12/1939238/BlackBerry-Code-Signing-Server-Outage)
- [r/blackberry: infrastructure end of life](https://reddit.fabiomanganiello.com/r/blackberry/comments/irlvzo/blackberry_10pbos_infrastructure_eol)
