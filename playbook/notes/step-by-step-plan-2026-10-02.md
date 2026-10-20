That settles it: **on a fresh flash of Psyden's image, Browser, Clock and Setup all work.** So his image is fine, and **something we did afterwards broke them**. We've already ruled out the app removals, the layout and the OpenSSL libraries themselves, so it's somewhere in the remaining steps. Now we can find out exactly which.

The password surviving the reflash isn't odd. The PlayBook keeps the device password in a protected area outside the partitions a flash rewrites, so it persists.

**Plan:** redo the setup **one step at a time**, with you opening the Browser after each step. The step that breaks it is the culprit:

| Step | What | Then test |
|---|---|---|
| 1 | You turn on Development Mode | Browser |
| 2 | I run the root script | Browser |
| 3 | I install your SSH key and apply the security fixes | Browser |
| 4 | I remove the bloat (one batch, one prompt at most) | Browser |
| 5 | I set your home-screen layout | Browser |
| 6 | I fix the Android runtime permissions (for Chroma Doze) | Browser + Chroma Doze |

The OpenSSL experiment stays out entirely. My main suspect is now **step 2 or 3**: the root process or something in my security changes. Every crash we saw was after root had run at least once.

**Start with step 1:** turn on Development Mode, test the Browser, and tell me the result.


Agreed. Here's the removal order, from least likely to affect other apps to most:

1. **Accessories Store**: just a link to a web store
2. **Help**
3. **Print To Go**
4. **PressReader**
5. **Weather**
6. **Music Store**
7. **App World**
8. **Bridge apps**, one by one: Bridge Apps 01–05, then BBM, SMS, Messages, Contacts, Calendar, Tasks, MemoPad
9. **Bridge Browser**: higher risk, since it's tied to the Browser
10. **`sys.bbbridge`**, the hidden Bridge service. **I'd keep this one.** It's actually the WebKit "Torch" launcher service, it has no icon, and removing it gains you nothing visible.

After each removal you test the Browser, so it's slower, but if something breaks we'll know exactly which app caused it. Each removal may bring a password prompt.

We start the removals after steps 1–3 check out. **First: turn on Development Mode, test the Browser, and tell me the result.**