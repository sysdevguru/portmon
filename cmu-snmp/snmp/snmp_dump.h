/* -*- c++ -*- */
#ifndef _SNMP_DUMP_H_
#define _SNMP_DUMP_H_

/**********************************************************************
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
 * $Id: snmp_dump.h,v 1.5 1998/05/06 04:07:33 ryan Exp $
 * 
 **********************************************************************/

#ifdef WIN32
#define DLLEXPORT __declspec(dllexport)
#else  /* WIN32 */
#define DLLEXPORT
#endif /* WIN32 */

#ifdef __cplusplus
extern "C" {
#endif

DLLEXPORT void snmp_dump_packet(int i);
DLLEXPORT void snmp_dump(u_char *, int, char *, struct in_addr);

#ifdef __cplusplus
}
#endif

#endif /* _SNMP_DUMP_H_ */
