/* -*- c++ -*- */
#ifndef _SNMP_API_ERROR_H_
#define _SNMP_API_ERROR_H_

/***************************************************************************
 *
 *           Copyright 1998 by Carnegie Mellon University
 * 
 *                       All Rights Reserved
 * 
 * Permission to use, copy, modify, and distribute this software and its
 * documentation for any purpose and without fee is hereby granted,
 * provided that the above copyright notice appear in all copies and that
 * both that copyright notice and this permission notice appear in
 * supporting documentation, and that the name of CMU not be
 * used in advertising or publicity pertaining to distribution of the
 * software without specific, written prior permission.
 * 
 * CMU DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
 * ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL
 * CMU BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR
 * ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
 * WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
 * ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
 * SOFTWARE.
 * 
 * Author: Ryan Troll <ryan+@andrew.cmu.edu>
 * 
 * $Id: snmp_api_error.h,v 1.6 1998/09/01 03:05:19 ryan Exp $
 * 
 ***************************************************************************/

/* Error return values */
#define SNMPERR_GENERR		-1
#define SNMPERR_BAD_LOCPORT	-2  /* local port was already in use */
#define SNMPERR_BAD_ADDRESS	-3
#define SNMPERR_BAD_SESSION	-4
#define SNMPERR_TOO_LONG	-5  /* data too long for provided buffer */

#define SNMPERR_ASN_ENCODE      -6
#define SNMPERR_ASN_DECODE      -7
#define SNMPERR_PDU_TRANSLATION -8
#define SNMPERR_OS_ERR          -9
#define SNMPERR_INVALID_TXTOID  -10

#define SNMPERR_UNABLE_TO_FIX   -11
#define SNMPERR_UNSUPPORTED_TYPE -12
#define SNMPERR_PDU_PARSE        -13
#define SNMPERR_PACKET_ERR      -14
#define SNMPERR_NO_RESPONSE     -15

#define SNMPERR_LAST            -16 /* Last error message */

#ifdef WIN32
#define DLLEXPORT __declspec(dllexport)
#else  /* WIN32 */
#define DLLEXPORT
#endif /* WIN32 */

#ifdef __cplusplus
extern "C" {
#endif

/* extern int snmp_errno */

DLLEXPORT char *snmp_api_error(int);
DLLEXPORT int   snmp_api_errno(void);

DLLEXPORT char *api_errstring(int); /* Backwards compatibility */
DLLEXPORT void snmp_set_api_error(int);

struct snmp_session;
DLLEXPORT void snmp_error(struct snmp_session *,int *,int *,char **);

#ifdef __cplusplus
}
#endif

#endif /* _SNMP_API_ERROR_H_ */
