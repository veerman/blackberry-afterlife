/* Force-included in every PlayBook (QNX 6.5) compile. */
#ifndef PLAYBOOK_QNX_COMPAT_H
#define PLAYBOOK_QNX_COMPAT_H
/* sys/select.h declares memset only in std:: and sets __MEMSET_DEFINED, which
 * then hides the global declaration in string.h. Pull string.h in first. */
#include <string.h>
/* math.h adds Dinkumware C++ overloads (pow(double,int), ...) that clash with
 * libstdc++ <cmath>. */
#define _NO_CPP_INLINES 1
#define _HAS_GENERIC_TEMPLATES 0
#endif
